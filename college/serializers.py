from django.contrib.auth.models import User
from rest_framework import serializers

from .models import (
    UserProfile, Student, Attendance, FeeTransaction,
    AccountTransaction, SalaryPayment,
)


class MeSerializer(serializers.ModelSerializer):
    role = serializers.SerializerMethodField()
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'full_name', 'email', 'role', 'is_superuser']

    def get_role(self, obj):
        if obj.is_superuser:
            return 'ADMIN'
        return obj.profile.role if hasattr(obj, 'profile') else 'STAFF'

    def get_full_name(self, obj):
        return obj.get_full_name() or obj.username


class StudentSerializer(serializers.ModelSerializer):
    full_name = serializers.ReadOnlyField()
    paid_fee = serializers.ReadOnlyField()
    pending_fee = serializers.ReadOnlyField()

    class Meta:
        model = Student
        fields = [
            'id', 'first_name', 'last_name', 'full_name', 'roll_number',
            'admission_number', 'class_name', 'batch', 'parent_phone',
            'total_course_fee', 'is_active', 'paid_fee', 'pending_fee',
        ]


class AttendanceSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.full_name', read_only=True)
    roll_number = serializers.CharField(source='student.roll_number', read_only=True)

    class Meta:
        model = Attendance
        fields = [
            'id', 'student', 'student_name', 'roll_number', 'date', 'period',
            'status', 'leave_reason', 'marked_by',
        ]
        read_only_fields = ['marked_by']


class FeeTransactionSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.full_name', read_only=True)
    roll_number = serializers.CharField(source='student.roll_number', read_only=True)

    class Meta:
        model = FeeTransaction
        fields = [
            'id', 'student', 'student_name', 'roll_number', 'amount_paid',
            'payment_date', 'payment_method', 'receipt_number', 'remarks',
        ]
        read_only_fields = ['receipt_number']


class AccountTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccountTransaction
        fields = [
            'id', 'transaction_type', 'category', 'amount', 'date',
            'payment_method', 'description',
        ]


class SalaryPaymentSerializer(serializers.ModelSerializer):
    staff_name = serializers.CharField(source='staff.get_full_name', read_only=True)

    class Meta:
        model = SalaryPayment
        fields = [
            'id', 'staff', 'staff_name', 'month', 'basic_salary',
            'advance_deducted', 'other_deductions', 'amount_paid',
            'payment_date', 'payment_status', 'remarks',
        ]


class StaffSerializer(serializers.ModelSerializer):
    phone = serializers.CharField(source='profile.phone', allow_blank=True, required=False)
    salary = serializers.DecimalField(source='profile.salary', max_digits=10, decimal_places=2, required=False)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'first_name', 'last_name', 'email',
            'is_active', 'phone', 'salary',
        ]

    def update(self, instance, validated_data):
        profile_data = validated_data.pop('profile', {})
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if profile_data and hasattr(instance, 'profile'):
            for attr, value in profile_data.items():
                setattr(instance.profile, attr, value)
            instance.profile.save()
        return instance


class StaffCreateSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)
    first_name = serializers.CharField()
    last_name = serializers.CharField(required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    phone = serializers.CharField(required=False, allow_blank=True)
    salary = serializers.DecimalField(max_digits=10, decimal_places=2, default=0)

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("A user with that username already exists.")
        return value

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            password=validated_data['password'],
            first_name=validated_data['first_name'],
            last_name=validated_data.get('last_name', ''),
            email=validated_data.get('email', ''),
        )
        UserProfile.objects.create(
            user=user,
            role='STAFF',
            phone=validated_data.get('phone', ''),
            salary=validated_data['salary'],
        )
        return user
