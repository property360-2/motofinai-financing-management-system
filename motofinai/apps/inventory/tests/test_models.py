from decimal import Decimal

from django.test import TestCase

from motofinai.apps.inventory.models import Motor, Stock


class StockModelTest(TestCase):
    """Tests for Stock model methods."""

    def setUp(self):
        """Create a Stock instance for testing."""
        self.stock = Stock.objects.create(
            brand="Yamaha",
            model_name="Mio",
            year=2024,
            color="Red",
            quantity_available=10,
            quantity_reserved=2,
            quantity_sold=5,
            quantity_repossessed=1,
        )

    def test_total_quantity(self):
        """Test that total_quantity property returns correct sum."""
        self.assertEqual(self.stock.total_quantity, 18)  # 10 + 2 + 5 + 1

    def test_mark_as_reserved_success(self):
        """Test successfully reserving stock."""
        initial_available = self.stock.quantity_available
        initial_reserved = self.stock.quantity_reserved

        self.stock.mark_as_reserved(amount=3)
        self.stock.refresh_from_db()

        self.assertEqual(self.stock.quantity_available, initial_available - 3)
        self.assertEqual(self.stock.quantity_reserved, initial_reserved + 3)

    def test_mark_as_reserved_insufficient_stock(self):
        """Test that reserving more than available raises ValueError."""
        with self.assertRaises(ValueError) as context:
            self.stock.mark_as_reserved(amount=15)  # Only 10 available

        self.assertIn("Insufficient available stock", str(context.exception))

    def test_mark_as_sold_from_available(self):
        """Test marking items as sold from available stock."""
        initial_available = self.stock.quantity_available
        initial_sold = self.stock.quantity_sold

        self.stock.mark_as_sold(amount=3)
        self.stock.refresh_from_db()

        self.assertEqual(self.stock.quantity_available, initial_available - 3)
        self.assertEqual(self.stock.quantity_sold, initial_sold + 3)

    def test_mark_as_sold_from_reserved(self):
        """Test marking items as sold from reserved stock when available is insufficient."""
        # Use up all available stock first
        self.stock.mark_as_sold(amount=10)
        self.stock.refresh_from_db()

        initial_reserved = self.stock.quantity_reserved
        initial_sold = self.stock.quantity_sold

        # Now sell from reserved
        self.stock.mark_as_sold(amount=2)
        self.stock.refresh_from_db()

        self.assertEqual(self.stock.quantity_reserved, initial_reserved - 2)
        self.assertEqual(self.stock.quantity_sold, initial_sold + 2)

    def test_mark_as_sold_insufficient_stock(self):
        """Test that selling more than available + reserved raises ValueError."""
        with self.assertRaises(ValueError) as context:
            self.stock.mark_as_sold(amount=20)  # Only 10 available + 2 reserved = 12

        self.assertIn("Insufficient stock for sale", str(context.exception))

    def test_mark_as_repossessed_success(self):
        """Test successfully repossessing sold items."""
        initial_sold = self.stock.quantity_sold
        initial_repossessed = self.stock.quantity_repossessed

        self.stock.mark_as_repossessed(amount=2)
        self.stock.refresh_from_db()

        self.assertEqual(self.stock.quantity_sold, initial_sold - 2)
        self.assertEqual(self.stock.quantity_repossessed, initial_repossessed + 2)

    def test_mark_as_repossessed_insufficient(self):
        """Test that repossessing more than sold raises ValueError."""
        with self.assertRaises(ValueError) as context:
            self.stock.mark_as_repossessed(amount=10)  # Only 5 sold

        self.assertIn("Cannot repossess more than sold", str(context.exception))

    def test_return_to_available_success(self):
        """Test returning repossessed items to available."""
        initial_repossessed = self.stock.quantity_repossessed
        initial_available = self.stock.quantity_available

        self.stock.return_to_available(amount=1)
        self.stock.refresh_from_db()

        self.assertEqual(self.stock.quantity_repossessed, initial_repossessed - 1)
        self.assertEqual(self.stock.quantity_available, initial_available + 1)

    def test_return_to_available_insufficient(self):
        """Test that returning more than repossessed raises ValueError."""
        with self.assertRaises(ValueError) as context:
            self.stock.return_to_available(amount=5)  # Only 1 repossessed

        self.assertIn("Cannot return more than repossessed", str(context.exception))

    def test_cancel_reservation_success(self):
        """Test successfully canceling reservations."""
        initial_reserved = self.stock.quantity_reserved
        initial_available = self.stock.quantity_available

        self.stock.cancel_reservation(amount=2)
        self.stock.refresh_from_db()

        self.assertEqual(self.stock.quantity_reserved, initial_reserved - 2)
        self.assertEqual(self.stock.quantity_available, initial_available + 2)

    def test_cancel_reservation_insufficient(self):
        """Test that canceling more than reserved raises ValueError."""
        with self.assertRaises(ValueError) as context:
            self.stock.cancel_reservation(amount=5)  # Only 2 reserved

        self.assertIn("Cannot cancel more than reserved", str(context.exception))

    def test_decrease_available_success(self):
        """Test successfully decreasing available stock."""
        initial_available = self.stock.quantity_available
        initial_sold = self.stock.quantity_sold

        self.stock.decrease_available(amount=3)
        self.stock.refresh_from_db()

        self.assertEqual(self.stock.quantity_available, initial_available - 3)
        self.assertEqual(self.stock.quantity_sold, initial_sold + 3)

    def test_decrease_available_insufficient(self):
        """Test that decreasing more than available raises ValueError."""
        with self.assertRaises(ValueError) as context:
            self.stock.decrease_available(amount=15)  # Only 10 available

        self.assertIn("Insufficient available stock", str(context.exception))

    def test_decrease_available_default_amount(self):
        """Test that decrease_available defaults to 1."""
        initial_available = self.stock.quantity_available

        self.stock.decrease_available()
        self.stock.refresh_from_db()

        self.assertEqual(self.stock.quantity_available, initial_available - 1)

    def test_increase_available_success(self):
        """Test successfully increasing available stock."""
        initial_available = self.stock.quantity_available
        initial_sold = self.stock.quantity_sold

        self.stock.increase_available(amount=2)
        self.stock.refresh_from_db()

        self.assertEqual(self.stock.quantity_available, initial_available + 2)
        self.assertEqual(self.stock.quantity_sold, initial_sold - 2)

    def test_increase_available_insufficient(self):
        """Test that increasing more than sold raises ValueError."""
        with self.assertRaises(ValueError) as context:
            self.stock.increase_available(amount=10)  # Only 5 sold

        self.assertIn("Cannot return more than sold", str(context.exception))

    def test_increase_available_default_amount(self):
        """Test that increase_available defaults to 1."""
        initial_sold = self.stock.quantity_sold

        self.stock.increase_available()
        self.stock.refresh_from_db()

        self.assertEqual(self.stock.quantity_sold, initial_sold - 1)

    def test_stock_operations_workflow(self):
        """Test a complete workflow of stock operations."""
        # Start fresh
        stock = Stock.objects.create(
            brand="Honda",
            model_name="Wave",
            year=2024,
            quantity_available=20,
        )

        # Reserve 5 units
        stock.mark_as_reserved(5)
        stock.refresh_from_db()
        self.assertEqual(stock.quantity_available, 15)
        self.assertEqual(stock.quantity_reserved, 5)

        # Sell 10 from available
        stock.decrease_available(10)
        stock.refresh_from_db()
        self.assertEqual(stock.quantity_available, 5)
        self.assertEqual(stock.quantity_sold, 10)

        # Sell remaining 5 from available
        stock.mark_as_sold(5)
        stock.refresh_from_db()
        self.assertEqual(stock.quantity_available, 0)  # Used up all 5 available
        self.assertEqual(stock.quantity_sold, 15)  # 10 + 5

        # Now sell 3 from reserved (since available is 0)
        stock.mark_as_sold(3)
        stock.refresh_from_db()
        self.assertEqual(stock.quantity_reserved, 2)  # Used 3 from reserved
        self.assertEqual(stock.quantity_sold, 18)  # 15 + 3

        # Repossess 2
        stock.mark_as_repossessed(2)
        stock.refresh_from_db()
        self.assertEqual(stock.quantity_sold, 16)
        self.assertEqual(stock.quantity_repossessed, 2)

        # Return repossessed to available
        stock.return_to_available(2)
        stock.refresh_from_db()
        self.assertEqual(stock.quantity_repossessed, 0)
        self.assertEqual(stock.quantity_available, 2)

        # Total should still be 20
        self.assertEqual(stock.total_quantity, 20)

    def test_stock_unique_together_constraint(self):
        """Test that brand, model_name, year, color must be unique together."""
        stock1 = Stock.objects.create(
            brand="Yamaha",
            model_name="Mio",
            year=2024,
            color="Blue",
            quantity_available=5,
        )

        # Attempting to create duplicate should raise IntegrityError
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            Stock.objects.create(
                brand="Yamaha",
                model_name="Mio",
                year=2024,
                color="Blue",
                quantity_available=10,
            )

    def test_stock_str_representation(self):
        """Test string representation of Stock."""
        # With color
        self.assertEqual(str(self.stock), "2024 Yamaha Mio (Red)")

        # Without color
        stock_no_color = Stock.objects.create(
            brand="Honda",
            model_name="Click",
            year=2023,
            quantity_available=5,
        )
        self.assertEqual(str(stock_no_color), "2023 Honda Click")


class MotorModelTest(TestCase):
    """Tests for Motor model."""

    def setUp(self):
        """Create a Motor instance for testing."""
        self.stock = Stock.objects.create(
            brand="Yamaha",
            model_name="Mio",
            year=2024,
            color="Red",
            quantity_available=10,
        )

        self.motor = Motor.objects.create(
            type=Motor.Type.SCOOTER,
            brand="Yamaha",
            model_name="Mio",
            year=2024,
            color="Red",
            chassis_number="ABC123",
            stock=self.stock,
            purchase_price=Decimal("75000.00"),
            quantity=1,
        )

    def test_motor_display_name(self):
        """Test motor display name property."""
        self.assertEqual(self.motor.display_name, "2024 Yamaha Mio")

    def test_motor_type_display(self):
        """Test motor type display property."""
        self.assertEqual(self.motor.type_display, "Scooter")

    def test_motor_str_representation(self):
        """Test string representation of Motor."""
        self.assertEqual(str(self.motor), "2024 Yamaha Mio")

    def test_motor_approval_status_default(self):
        """Test that default approval status is PENDING."""
        self.assertEqual(self.motor.approval_status, Motor.ApprovalStatus.PENDING)

    def test_motor_unique_together_constraint(self):
        """Test that brand, model_name, year, chassis_number must be unique together."""
        # Attempting to create duplicate should raise IntegrityError
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            Motor.objects.create(
                type=Motor.Type.SCOOTER,
                brand="Yamaha",
                model_name="Mio",
                year=2024,
                chassis_number="ABC123",  # Same chassis number
                stock=self.stock,
                purchase_price=Decimal("75000.00"),
            )
