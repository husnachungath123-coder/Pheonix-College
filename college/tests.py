from django.test import TestCase
from django.contrib.auth.models import User
from college.models import UserProfile, Student, FeeTransaction, AccountTransaction

class CollegeModelAndPermissionTests(TestCase):
    def setUp(self):
        # Create an Admin User
        self.admin_user = User.objects.create_user(username='admin_test', password='password123')
        UserProfile.objects.create(user=self.admin_user, role='ADMIN')

        # Create a Staff User
        self.staff_user = User.objects.create_user(username='staff_test', password='password123')
        UserProfile.objects.create(user=self.staff_user, role='STAFF')

        # Create a Student
        self.student = Student.objects.create(
            first_name='Anil',
            last_name='Kumar',
            roll_number='BCA-test-01',
            admission_number='ADM-test-100',
            class_name='BCA',
            batch='2024-2027',
            parent_phone='+919999999999',
            total_course_fee=50000.00
        )

    def test_fee_calculations(self):
        """Test that student paid and pending fees are computed accurately."""
        # Initial status
        self.assertEqual(float(self.student.paid_fee), 0.00)
        self.assertEqual(float(self.student.pending_fee), 50000.00)

        # Log a payment
        FeeTransaction.objects.create(
            student=self.student,
            amount_paid=15000.00,
            payment_date='2026-07-08',
            payment_method='CASH'
        )

        # Updated status
        self.assertEqual(float(self.student.paid_fee), 15000.00)
        self.assertEqual(float(self.student.pending_fee), 35000.00)

    def test_accounts_restrictions_for_staff(self):
        """Test that teachers/staff cannot access financial daily accounts page."""
        # Log in as Staff
        self.client.login(username='staff_test', password='password123')
        
        # Staff request accounts page
        response = self.client.get('/accounts/')
        
        # Staff should be redirected to the dashboard (root URL '/')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url.split('?')[0], '/')

    def test_accounts_access_for_admin(self):
        """Test that Super Admin has access to the daily accounts page."""
        # Log in as Admin
        self.client.login(username='admin_test', password='password123')
        
        # Admin request accounts page
        response = self.client.get('/accounts/')
        
        # Admin should access the accounts page successfully
        self.assertEqual(response.status_code, 200)
