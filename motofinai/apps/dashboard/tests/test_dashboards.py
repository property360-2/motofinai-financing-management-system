"""
Tests for dashboard views and KPI calculations
"""
from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model

from motofinai.apps.dashboard.kpi import AdminDashboardKPI, FinanceDashboardKPI

User = get_user_model()


class DashboardKPITestCase(TestCase):
    """Test KPI calculation utilities"""

    def test_loan_kpis_empty(self):
        """Test loan KPIs with no data"""
        kpis = AdminDashboardKPI.get_loan_kpis()

        self.assertEqual(kpis['total_loans'], 0)
        self.assertEqual(kpis['active_loans'], 0)
        self.assertEqual(kpis['pending_loans'], 0)
        self.assertEqual(kpis['total_loan_value'], Decimal('0'))

    def test_payment_kpis_empty(self):
        """Test payment KPIs with no data"""
        kpis = AdminDashboardKPI.get_payment_kpis()

        self.assertIsInstance(kpis['total_collected'], Decimal)
        self.assertIsInstance(kpis['pending_amount'], Decimal)
        self.assertIsInstance(kpis['overdue_amount'], Decimal)
        self.assertGreaterEqual(kpis['overdue_count'], 0)

    def test_risk_kpis_empty(self):
        """Test risk KPIs with no data"""
        kpis = AdminDashboardKPI.get_risk_kpis()

        self.assertEqual(kpis['total_assessments'], 0)
        self.assertEqual(kpis['low_risk'], 0)
        self.assertEqual(kpis['medium_risk'], 0)
        self.assertEqual(kpis['high_risk'], 0)

    def test_inventory_kpis_empty(self):
        """Test inventory KPIs with no data"""
        kpis = AdminDashboardKPI.get_inventory_kpis()

        self.assertEqual(kpis['total_units'], 0)
        self.assertEqual(kpis['available'], 0)
        self.assertEqual(kpis['total_value'], Decimal('0'))

    def test_user_kpis(self):
        """Test user KPI calculations"""
        # Create test users
        User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='testpass123',
            role=User.Roles.ADMIN
        )
        User.objects.create_user(
            username='finance',
            email='finance@test.com',
            password='testpass123',
            role=User.Roles.FINANCE
        )

        kpis = AdminDashboardKPI.get_user_kpis()

        self.assertEqual(kpis['total_users'], 2)
        self.assertEqual(kpis['active_users'], 2)
        self.assertEqual(kpis['admin_users'], 1)
        self.assertEqual(kpis['finance_users'], 1)

    def test_admin_dashboard_kpis(self):
        """Test admin dashboard aggregated KPIs"""
        kpis = AdminDashboardKPI.get_all_kpis()

        self.assertIn('loans', kpis)
        self.assertIn('payments', kpis)
        self.assertIn('risk', kpis)
        self.assertIn('repossession', kpis)
        self.assertIn('inventory', kpis)
        self.assertIn('users', kpis)
        self.assertIn('audit', kpis)
        self.assertIn('recent_activities', kpis)

    def test_finance_dashboard_kpis(self):
        """Test finance dashboard aggregated KPIs"""
        kpis = FinanceDashboardKPI.get_all_kpis()

        self.assertIn('loans', kpis)
        self.assertIn('payments', kpis)
        self.assertIn('risk', kpis)
        self.assertIn('repossession', kpis)
        self.assertIn('recent_activities', kpis)


class AdminDashboardViewTestCase(TestCase):
    """Test admin dashboard view"""

    def setUp(self):
        self.client = Client()
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='testpass123',
            role=User.Roles.ADMIN
        )

    def test_admin_dashboard_access_by_admin(self):
        """Test admin can access admin dashboard"""
        self.client.login(username='admin', password='testpass123')
        response = self.client.get(reverse('dashboard:admin'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'pages/dashboard/admin_dashboard.html')

    def test_admin_dashboard_context_data(self):
        """Test admin dashboard context contains KPIs"""
        self.client.login(username='admin', password='testpass123')
        response = self.client.get(reverse('dashboard:admin'))

        self.assertIn('kpis', response.context)
        self.assertIn('page_title', response.context)
        self.assertIn('current_month', response.context)

    def test_admin_dashboard_requires_login(self):
        """Test admin dashboard requires authentication"""
        response = self.client.get(reverse('dashboard:admin'))
        self.assertEqual(response.status_code, 302)  # Redirect to login


class FinanceDashboardViewTestCase(TestCase):
    """Test finance dashboard view"""

    def setUp(self):
        self.client = Client()
        self.finance_user = User.objects.create_user(
            username='finance',
            email='finance@test.com',
            password='testpass123',
            role=User.Roles.FINANCE
        )
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='testpass123',
            role=User.Roles.ADMIN
        )

    def test_finance_dashboard_access_by_finance(self):
        """Test finance user can access finance dashboard"""
        self.client.login(username='finance', password='testpass123')
        response = self.client.get(reverse('dashboard:finance'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'pages/dashboard/finance_dashboard.html')

    def test_finance_dashboard_access_by_admin(self):
        """Test admin can also access finance dashboard"""
        self.client.login(username='admin', password='testpass123')
        response = self.client.get(reverse('dashboard:finance'))
        self.assertEqual(response.status_code, 200)

    def test_finance_dashboard_context_data(self):
        """Test finance dashboard context contains KPIs"""
        self.client.login(username='finance', password='testpass123')
        response = self.client.get(reverse('dashboard:finance'))

        self.assertIn('kpis', response.context)
        self.assertIn('page_title', response.context)
        self.assertIn('current_month', response.context)

    def test_finance_dashboard_requires_login(self):
        """Test finance dashboard requires authentication"""
        response = self.client.get(reverse('dashboard:finance'))
        self.assertEqual(response.status_code, 302)  # Redirect to login


class ReportExportTestCase(TestCase):
    """Test report export functionality"""

    def setUp(self):
        self.client = Client()
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='testpass123',
            role=User.Roles.ADMIN
        )
        self.finance_user = User.objects.create_user(
            username='finance',
            email='finance@test.com',
            password='testpass123',
            role=User.Roles.FINANCE
        )

    def test_export_loans_requires_login(self):
        """Test loan export requires authentication"""
        response = self.client.get(reverse('dashboard:export_loans'))
        self.assertEqual(response.status_code, 302)

    def test_export_loans_by_admin(self):
        """Test admin can export loans"""
        self.client.login(username='admin', password='testpass123')
        response = self.client.get(reverse('dashboard:export_loans'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response['Content-Type'],
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

    def test_export_payments_by_finance(self):
        """Test finance user can export payments"""
        self.client.login(username='finance', password='testpass123')
        response = self.client.get(reverse('dashboard:export_payments'))
        self.assertEqual(response.status_code, 200)

    def test_export_risk_by_finance(self):
        """Test finance user can export risk assessments"""
        self.client.login(username='finance', password='testpass123')
        response = self.client.get(reverse('dashboard:export_risk'))
        self.assertEqual(response.status_code, 200)

    def test_export_inventory_by_admin(self):
        """Test admin can export inventory"""
        self.client.login(username='admin', password='testpass123')
        response = self.client.get(reverse('dashboard:export_inventory'))
        self.assertEqual(response.status_code, 200)
