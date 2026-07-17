from django.db import models
from django.contrib.auth.models import User
from django.db.models import Sum
import uuid

class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('ADMIN', 'Super Admin'),
        ('STAFF', 'Staff/Teacher'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='STAFF')
    phone = models.CharField(max_length=15, blank=True, null=True)
    salary = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} ({self.get_role_display()})"

class Student(models.Model):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    roll_number = models.CharField(max_length=20, unique=True)
    admission_number = models.CharField(max_length=20, unique=True)
    class_name = models.CharField(max_length=50)  # e.g. BCA, BCom, MCA
    batch = models.CharField(max_length=20)       # e.g. 2024-2027
    parent_phone = models.CharField(max_length=15)
    total_course_fee = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.roll_number})"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def paid_fee(self):
        result = self.fee_transactions.aggregate(total=Sum('amount_paid'))['total']
        return result or 0.00

    @property
    def pending_fee(self):
        return float(self.total_course_fee) - float(self.paid_fee)


class Attendance(models.Model):
    STATUS_CHOICES = [
        ('PRESENT', 'Present'),
        ('ABSENT', 'Absent'),
        ('LEAVE', 'On Leave'),
    ]
    PERIOD_CHOICES = [
        ('Daily', 'Daily'),
        ('Period 1', 'Period 1'),
        ('Period 2', 'Period 2'),
        ('Period 3', 'Period 3'),
        ('Period 4', 'Period 4'),
        ('Period 5', 'Period 5'),
    ]
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='attendances')
    date = models.DateField()
    period = models.CharField(max_length=20, choices=PERIOD_CHOICES, default='Daily')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    marked_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='marked_attendances')
    leave_reason = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ('student', 'date', 'period')

    def __str__(self):
        return f"{self.student.roll_number} - {self.date} ({self.period}): {self.status}"


class FeeTransaction(models.Model):
    METHOD_CHOICES = [
        ('CASH', 'Cash in Hand'),
        ('BANK', 'Bank/UPI'),
    ]
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='fee_transactions')
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateField()
    payment_method = models.CharField(max_length=10, choices=METHOD_CHOICES)
    receipt_number = models.CharField(max_length=50, unique=True, blank=True)
    remarks = models.TextField(blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.receipt_number:
            self.receipt_number = f"REC-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.receipt_number} - {self.student.roll_number} - {self.amount_paid}"


class AccountTransaction(models.Model):
    TYPE_CHOICES = [
        ('INCOME', 'Income'),
        ('EXPENSE', 'Expense'),
    ]
    METHOD_CHOICES = [
        ('CASH', 'Cash in Hand'),
        ('BANK', 'Bank/UPI'),
    ]
    transaction_type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    category = models.CharField(max_length=50)  # Course Fees, Rent, Salary, Bill, etc.
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField()
    payment_method = models.CharField(max_length=10, choices=METHOD_CHOICES)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"[{self.transaction_type}] {self.category} - {self.amount} ({self.date})"


class SalaryPayment(models.Model):
    STATUS_CHOICES = [
        ('PAID', 'Paid'),
        ('PENDING', 'Pending'),
    ]
    staff = models.ForeignKey(User, on_delete=models.CASCADE, related_name='salary_payments')
    month = models.CharField(max_length=20)  # e.g. "2026-06"
    basic_salary = models.DecimalField(max_digits=10, decimal_places=2)
    advance_deducted = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    other_deductions = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateField()
    payment_status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PAID')
    remarks = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.staff.username} - {self.month} - {self.amount_paid}"
