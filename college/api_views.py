from datetime import datetime, timedelta

from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.db.models import Sum
from django.utils import timezone
from rest_framework import generics, status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import (
    AccountTransaction, Attendance, FeeTransaction, SalaryPayment, Student,
)
from .serializers import (
    AccountTransactionSerializer, AttendanceSerializer,
    FeeTransactionSerializer, MeSerializer, SalaryPaymentSerializer,
    StaffCreateSerializer, StaffSerializer, StudentSerializer,
)


def is_admin(user):
    if user.is_superuser:
        return True
    return hasattr(user, 'profile') and user.profile.role == 'ADMIN'


class IsAdmin(IsAuthenticated):
    def has_permission(self, request, view):
        return super().has_permission(request, view) and is_admin(request.user)


class IsAdminForWrite(IsAuthenticated):
    """Allow any authenticated user to read (list/retrieve), but only admins may
    create, update, or delete records. Staff can see students/fees but cannot
    create, modify, or remove them — that's an admin-only action.

    (Previously this only gated POST, which meant any authenticated staff
    account could PUT/PATCH/DELETE arbitrary student or fee records — an
    IDOR / broken-access-control bug. Now every unsafe method requires admin.)
    """

    SAFE_METHODS = ('GET', 'HEAD', 'OPTIONS')

    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
        if request.method in self.SAFE_METHODS:
            return True
        return is_admin(request.user)


# ----------------- AUTH -----------------
@api_view(['POST'])
@permission_classes([AllowAny])
def login_api(request):
    username = request.data.get('username')
    password = request.data.get('password')
    user = authenticate(username=username, password=password)
    if user is None:
        return Response({'detail': 'Invalid username or password.'}, status=status.HTTP_400_BAD_REQUEST)
    if not user.is_active:
        return Response({'detail': 'This account has been deactivated.'}, status=status.HTTP_400_BAD_REQUEST)
    token, _ = Token.objects.get_or_create(user=user)
    return Response({'token': token.key, 'user': MeSerializer(user).data})


@api_view(['POST'])
def logout_api(request):
    request.user.auth_token.delete()
    return Response({'detail': 'Logged out.'})


@api_view(['GET'])
def me_api(request):
    return Response(MeSerializer(request.user).data)


# ----------------- DASHBOARD -----------------
@api_view(['GET'])
def dashboard_api(request):
    user = request.user
    role = user.profile.role if hasattr(user, 'profile') else 'STAFF'
    if user.is_superuser:
        role = 'ADMIN'
    today = timezone.localtime(timezone.now()).date()

    total_students = Student.objects.filter(is_active=True).count()

    total_marked_today = Attendance.objects.filter(date=today, period='Daily').count()
    present_today = Attendance.objects.filter(date=today, period='Daily', status='PRESENT').count()
    absent_today = Attendance.objects.filter(date=today, period='Daily', status='ABSENT').count()
    leave_today = Attendance.objects.filter(date=today, period='Daily', status='LEAVE').count()
    attendance_rate = round((present_today / total_marked_today) * 100, 1) if total_marked_today else 0

    data = {
        'role': role,
        'total_students': total_students,
        'attendance_rate': attendance_rate,
        'present_today': present_today,
        'absent_today': absent_today,
        'leave_today': leave_today,
        'cash_in_hand': 0, 'cash_in_bank': 0, 'total_balance': 0,
        'defaulters_count': 0, 'income_today': 0, 'expense_today': 0,
        'chart_months': [], 'chart_income': [], 'chart_expense': [],
    }

    if role == 'ADMIN':
        income_cash = AccountTransaction.objects.filter(transaction_type='INCOME', payment_method='CASH').aggregate(t=Sum('amount'))['t'] or 0
        expense_cash = AccountTransaction.objects.filter(transaction_type='EXPENSE', payment_method='CASH').aggregate(t=Sum('amount'))['t'] or 0
        cash_in_hand = income_cash - expense_cash

        income_bank = AccountTransaction.objects.filter(transaction_type='INCOME', payment_method='BANK').aggregate(t=Sum('amount'))['t'] or 0
        expense_bank = AccountTransaction.objects.filter(transaction_type='EXPENSE', payment_method='BANK').aggregate(t=Sum('amount'))['t'] or 0
        cash_in_bank = income_bank - expense_bank

        all_students = Student.objects.filter(is_active=True)
        defaulters_count = sum(1 for s in all_students if s.pending_fee > 0)

        income_today = AccountTransaction.objects.filter(transaction_type='INCOME', date=today).aggregate(t=Sum('amount'))['t'] or 0
        expense_today = AccountTransaction.objects.filter(transaction_type='EXPENSE', date=today).aggregate(t=Sum('amount'))['t'] or 0

        chart_months, chart_income, chart_expense = [], [], []
        for i in range(5, -1, -1):
            target_month = today - timedelta(days=30 * i)
            inc = AccountTransaction.objects.filter(transaction_type='INCOME', date__month=target_month.month, date__year=target_month.year).aggregate(t=Sum('amount'))['t'] or 0
            exp = AccountTransaction.objects.filter(transaction_type='EXPENSE', date__month=target_month.month, date__year=target_month.year).aggregate(t=Sum('amount'))['t'] or 0
            chart_months.append(target_month.strftime('%b'))
            chart_income.append(float(inc))
            chart_expense.append(float(exp))

        data.update({
            'cash_in_hand': float(cash_in_hand), 'cash_in_bank': float(cash_in_bank),
            'total_balance': float(cash_in_hand + cash_in_bank),
            'defaulters_count': defaulters_count,
            'income_today': float(income_today), 'expense_today': float(expense_today),
            'chart_months': chart_months, 'chart_income': chart_income, 'chart_expense': chart_expense,
        })

    return Response(data)


# ----------------- STUDENTS -----------------
class StudentViewSet(viewsets.ModelViewSet):
    serializer_class = StudentSerializer
    queryset = Student.objects.all().order_by('class_name', 'roll_number')
    permission_classes = [IsAdminForWrite]

    def get_queryset(self):
        qs = Student.objects.filter(is_active=True).order_by('class_name', 'roll_number')
        params = self.request.query_params
        if params.get('class_name'):
            qs = qs.filter(class_name__iexact=params['class_name'])
        if params.get('batch'):
            qs = qs.filter(batch__iexact=params['batch'])
        if params.get('search'):
            from django.db.models import Q
            s = params['search']
            qs = qs.filter(
                Q(first_name__icontains=s) | Q(last_name__icontains=s) |
                Q(roll_number__icontains=s) | Q(admission_number__icontains=s)
            )
        return qs

    def perform_destroy(self, instance):
        instance.delete()


# ----------------- ATTENDANCE -----------------
@api_view(['GET'])
def attendance_list_api(request):
    today = timezone.localtime(timezone.now()).date()
    date_str = request.query_params.get('date', today.strftime('%Y-%m-%d'))
    selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    period = request.query_params.get('period', 'Daily')
    class_filter = request.query_params.get('class_name', '')
    batch_filter = request.query_params.get('batch', '')

    students = Student.objects.filter(is_active=True)
    if class_filter:
        students = students.filter(class_name__iexact=class_filter)
    if batch_filter:
        students = students.filter(batch__iexact=batch_filter)

    existing = Attendance.objects.filter(date=selected_date, period=period)
    att_map = {a.student_id: a.status for a in existing}
    reason_map = {a.student_id: a.leave_reason or '' for a in existing}

    results = [{
        'id': s.id,
        'full_name': s.full_name,
        'roll_number': s.roll_number,
        'class_name': s.class_name,
        'batch': s.batch,
        'status': att_map.get(s.id, 'PRESENT'),
        'leave_reason': reason_map.get(s.id, ''),
    } for s in students]

    return Response({
        'date': date_str,
        'period': period,
        'students': results,
        'classes': list(Student.objects.values_list('class_name', flat=True).distinct()),
        'batches': list(Student.objects.values_list('batch', flat=True).distinct()),
    })


@api_view(['POST'])
def attendance_save_api(request):
    """Body: { date, period, records: [{student_id, status, leave_reason}] }"""
    date_str = request.data.get('date')
    period = request.data.get('period', 'Daily')
    records = request.data.get('records', [])
    selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()

    for rec in records:
        Attendance.objects.update_or_create(
            student_id=rec['student_id'],
            date=selected_date,
            period=period,
            defaults={
                'status': rec.get('status', 'PRESENT'),
                'leave_reason': rec.get('leave_reason', '') if rec.get('status') == 'LEAVE' else '',
                'marked_by': request.user,
            }
        )
    return Response({'detail': f'Attendance saved for {date_str} ({period}).'})


@api_view(['GET'])
def leaves_api(request):
    leaves = Attendance.objects.filter(status='LEAVE').select_related('student').order_by('-date')[:50]
    return Response(AttendanceSerializer(leaves, many=True).data)


# ----------------- FEES -----------------
class FeeTransactionViewSet(viewsets.ModelViewSet):
    serializer_class = FeeTransactionSerializer
    queryset = FeeTransaction.objects.all().select_related('student').order_by('-payment_date')
    permission_classes = [IsAdminForWrite]

    def get_queryset(self):
        qs = FeeTransaction.objects.all().select_related('student').order_by('-payment_date')
        student_id = self.request.query_params.get('student')
        if student_id:
            qs = qs.filter(student_id=student_id)
        return qs


@api_view(['GET'])
def fee_defaulters_api(request):
    students = Student.objects.filter(is_active=True)
    data = [{
        'id': s.id, 'full_name': s.full_name, 'roll_number': s.roll_number,
        'class_name': s.class_name, 'batch': s.batch, 'parent_phone': s.parent_phone,
        'total_course_fee': float(s.total_course_fee), 'paid_fee': float(s.paid_fee),
        'pending_fee': float(s.pending_fee),
    } for s in students if s.pending_fee > 0]
    return Response(data)


# ----------------- ACCOUNTS -----------------
class AccountTransactionViewSet(viewsets.ModelViewSet):
    serializer_class = AccountTransactionSerializer
    queryset = AccountTransaction.objects.all().order_by('-date')
    permission_classes = [IsAdmin]


# ----------------- SALARY -----------------
class SalaryPaymentViewSet(viewsets.ModelViewSet):
    serializer_class = SalaryPaymentSerializer
    queryset = SalaryPayment.objects.all().select_related('staff').order_by('-payment_date')
    permission_classes = [IsAdmin]


# ----------------- STAFF (admin only) -----------------
class StaffViewSet(viewsets.ModelViewSet):
    serializer_class = StaffSerializer
    permission_classes = [IsAdmin]
    queryset = User.objects.filter(profile__role='STAFF').select_related('profile').order_by('first_name')

    def create(self, request, *args, **kwargs):
        serializer = StaffCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(StaffSerializer(user).data, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([IsAdmin])
def staff_set_password_api(request, pk):
    staff_user = User.objects.get(pk=pk, profile__role='STAFF')
    new_password = request.data.get('new_password')
    if not new_password or len(new_password) < 6:
        return Response({'detail': 'Password must be at least 6 characters.'}, status=400)
    staff_user.set_password(new_password)
    staff_user.save()
    return Response({'detail': 'Password updated.'})


@api_view(['POST'])
@permission_classes([IsAdmin])
def staff_toggle_active_api(request, pk):
    staff_user = User.objects.get(pk=pk, profile__role='STAFF')
    staff_user.is_active = not staff_user.is_active
    staff_user.save()
    return Response(StaffSerializer(staff_user).data)
