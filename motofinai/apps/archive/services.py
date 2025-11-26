"""Services for archive restoration."""
from __future__ import annotations

from typing import Any, Dict
from django.apps import apps
from django.core.exceptions import ValidationError
from django.db import transaction

from motofinai.apps.inventory.models import Motor, Stock
from motofinai.apps.loans.models import LoanApplication, FinancingTerm
from motofinai.apps.payments.models import Payment


# Map module names to model classes
MODULE_MODEL_MAP = {
    "motors": Motor,
    "stocks": Stock,
    "loan_applications": LoanApplication,
    "financing_terms": FinancingTerm,
    "payments": Payment,
}


class ArchiveRestoreError(Exception):
    """Exception raised when archive restoration fails."""
    pass


def restore_record(module: str, data_snapshot: Dict[str, Any], original_record_id: int) -> Any:
    """
    Restore an archived record from its data snapshot.

    Args:
        module: Module name (e.g., 'motors', 'loan_applications')
        data_snapshot: JSON snapshot of the original record
        original_record_id: The original record ID

    Returns:
        The restored model instance

    Raises:
        ArchiveRestoreError: If restoration fails
    """
    # Get the model class for this module
    model_class = MODULE_MODEL_MAP.get(module)

    if not model_class:
        raise ArchiveRestoreError(
            f"Unsupported module: {module}. "
            f"Supported modules are: {', '.join(MODULE_MODEL_MAP.keys())}"
        )

    # Check if a record with this ID already exists
    if model_class.objects.filter(pk=original_record_id).exists():
        raise ArchiveRestoreError(
            f"Cannot restore: A {module} record with ID {original_record_id} already exists. "
            "Delete the existing record first or restore to a new ID."
        )

    try:
        with transaction.atomic():
            # Prepare data for restoration
            restore_data = prepare_restore_data(model_class, data_snapshot, original_record_id)

            # Create the restored record
            restored_instance = model_class(**restore_data)

            # Validate before saving
            restored_instance.full_clean()
            restored_instance.save()

            return restored_instance

    except ValidationError as e:
        error_messages = []
        if hasattr(e, 'message_dict'):
            for field, errors in e.message_dict.items():
                error_messages.extend([f"{field}: {err}" for err in errors])
        else:
            error_messages = e.messages
        raise ArchiveRestoreError(
            f"Validation error during restoration: {'; '.join(error_messages)}"
        )
    except Exception as e:
        raise ArchiveRestoreError(f"Unexpected error during restoration: {str(e)}")


def prepare_restore_data(model_class, data_snapshot: Dict[str, Any], original_record_id: int) -> Dict[str, Any]:
    """
    Prepare data snapshot for restoration by handling special fields.

    Args:
        model_class: The Django model class
        data_snapshot: The JSON snapshot data
        original_record_id: The original record ID

    Returns:
        Cleaned data ready for model instantiation
    """
    restore_data = data_snapshot.copy()

    # Set the original ID
    restore_data['id'] = original_record_id

    # Get model fields
    model_fields = {f.name: f for f in model_class._meta.get_fields()}

    # Handle special field types
    for field_name, value in list(restore_data.items()):
        if field_name not in model_fields:
            # Remove fields that don't exist in the model
            del restore_data[field_name]
            continue

        field = model_fields[field_name]

        # Handle auto-created fields that shouldn't be set manually
        if field_name in ['created_at', 'updated_at'] and getattr(field, 'auto_now_add', False) or getattr(field, 'auto_now', False):
            # For auto fields, let Django handle them unless explicitly preserving timestamps
            # We'll keep them to maintain historical accuracy
            pass

        # Handle ForeignKey fields - ensure we're storing the ID
        if hasattr(field, 'related_model') and field.many_to_one:
            # If value is None, keep it as None
            if value is None:
                continue
            # If value is a dict (nested object), extract the ID
            if isinstance(value, dict) and 'id' in value:
                restore_data[field_name] = value['id']
            # Otherwise assume it's already an ID
            elif isinstance(value, (int, str)):
                restore_data[field_name] = value

        # Handle ManyToMany fields (skip them for now, can be added post-restore if needed)
        if hasattr(field, 'related_model') and field.many_to_many:
            del restore_data[field_name]

    # Remove reverse relations
    for field_name in list(restore_data.keys()):
        field = model_fields.get(field_name)
        if field and hasattr(field, 'related_model') and field.one_to_many:
            del restore_data[field_name]

    return restore_data
