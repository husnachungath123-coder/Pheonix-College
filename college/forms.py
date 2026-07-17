from django import forms
from django.contrib.auth.models import User
from .models import Student, Attendance, FeeTransaction, AccountTransaction, SalaryPayment

class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ['first_name', 'last_name', 'roll_number', 'admission_number', 'class_name', 'batch', 'parent_phone', 'total_course_fee', 'is_active']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'}),
            'roll_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Roll Number'}),
            'admission_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Admission Number'}),
            'class_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. BCA, BCom'}),
            'batch': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 2024-2027'}),
            'parent_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Parent phone number'}),
            'total_course_fee': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Total Course Fee'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class LeaveForm(forms.ModelForm):
    class Meta:
        model = Attendance
        fields = ['student', 'date', 'period', 'leave_reason']
        widgets = {
            'student': forms.Select(attrs={'class': 'form-select select2-enable'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'period': forms.Select(attrs={'class': 'form-select'}),
            'leave_reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Reason for leave...'}),
        }

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.status = 'LEAVE'
        if commit:
            instance.save()
        return instance

class FeePaymentForm(forms.ModelForm):
    class Meta:
        model = FeeTransaction
        fields = ['student', 'amount_paid', 'payment_date', 'payment_method', 'remarks']
        widgets = {
            'student': forms.Select(attrs={'class': 'form-select select2-enable'}),
            'amount_paid': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Amount to pay'}),
            'payment_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'payment_method': forms.Select(attrs={'class': 'form-select'}),
            'remarks': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Optional remarks...'}),
        }

class AccountTransactionForm(forms.ModelForm):
    class Meta:
        model = AccountTransaction
        fields = ['transaction_type', 'category', 'amount', 'date', 'payment_method', 'description']
        widgets = {
            'transaction_type': forms.Select(attrs={'class': 'form-select'}),
            'category': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Rent, Electricity, Stationery'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Amount'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'payment_method': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Description...'}),
        }

class SalaryPaymentForm(forms.ModelForm):
    class Meta:
        model = SalaryPayment
        fields = ['staff', 'month', 'basic_salary', 'advance_deducted', 'other_deductions', 'amount_paid', 'payment_date', 'payment_status', 'remarks']
        widgets = {
            'staff': forms.Select(attrs={'class': 'form-select'}),
            'month': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 2026-07'}),
            'basic_salary': forms.NumberInput(attrs={'class': 'form-control'}),
            'advance_deducted': forms.NumberInput(attrs={'class': 'form-control'}),
            'other_deductions': forms.NumberInput(attrs={'class': 'form-control'}),
            'amount_paid': forms.NumberInput(attrs={'class': 'form-control'}),
            'payment_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'payment_status': forms.Select(attrs={'class': 'form-select'}),
            'remarks': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Optional remarks...'}),
        }


# ---- Staff Management Forms ----

from .models import UserProfile

class StaffCreateForm(forms.Form):
    """Form to create a new staff user + profile in one step."""
    first_name  = forms.CharField(max_length=50,  widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'}))
    last_name   = forms.CharField(max_length=50,  widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'}))
    username    = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Login Username'}))
    email       = forms.EmailField(required=False, widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email (optional)'}))
    phone       = forms.CharField(max_length=15, required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone number'}))
    salary      = forms.DecimalField(max_digits=10, decimal_places=2, initial=0,
                                     widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Monthly Basic Salary'}))
    password    = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Set password'}))
    password2   = forms.CharField(label='Confirm Password',
                                  widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Repeat password'}))

    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("This username is already taken.")
        return username

    def clean(self):
        cleaned = super().clean()
        p1, p2 = cleaned.get('password'), cleaned.get('password2')
        if p1 and p2 and p1 != p2:
            self.add_error('password2', "Passwords do not match.")
        return cleaned


class StaffEditForm(forms.Form):
    """Form to edit an existing staff user's profile details."""
    first_name = forms.CharField(max_length=50,  widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name  = forms.CharField(max_length=50,  widget=forms.TextInput(attrs={'class': 'form-control'}))
    email      = forms.EmailField(required=False, widget=forms.EmailInput(attrs={'class': 'form-control'}))
    phone      = forms.CharField(max_length=15, required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone number'}))
    salary     = forms.DecimalField(max_digits=10, decimal_places=2,
                                    widget=forms.NumberInput(attrs={'class': 'form-control'}))


class StaffPasswordForm(forms.Form):
    """Form to reset a staff member's password."""
    new_password  = forms.CharField(label='New Password',
                                    widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'New password'}))
    new_password2 = forms.CharField(label='Confirm New Password',
                                    widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Repeat new password'}))

    def clean(self):
        cleaned = super().clean()
        p1, p2 = cleaned.get('new_password'), cleaned.get('new_password2')
        if p1 and p2 and p1 != p2:
            self.add_error('new_password2', "Passwords do not match.")
        return cleaned
