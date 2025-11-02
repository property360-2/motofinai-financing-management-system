from django import forms


class RepossessionReminderForm(forms.Form):
    message = forms.CharField(
        label="Reminder message",
        widget=forms.Textarea(attrs={"rows": 4}),
        help_text="Notes about the reminder sent to the customer.",
    )


class RepossessionCloseForm(forms.Form):
    notes = forms.CharField(
        label="Resolution notes",
        widget=forms.Textarea(attrs={"rows": 4}),
        help_text="Summarize how the case was resolved before closure.",
    )
