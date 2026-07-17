from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Students
    path('students/', views.student_list, name='student_list'),
    path('students/add/', views.student_add, name='student_add'),
    path('students/<int:pk>/edit/', views.student_edit, name='student_edit'),
    path('students/<int:pk>/delete/', views.student_delete, name='student_delete'),

    # Staff (Admin only)
    path('staff/', views.staff_list, name='staff_list'),
    path('staff/add/', views.staff_add, name='staff_add'),
    path('staff/<int:pk>/edit/', views.staff_edit, name='staff_edit'),
    path('staff/<int:pk>/password/', views.staff_set_password, name='staff_set_password'),
    path('staff/<int:pk>/toggle/', views.staff_toggle_active, name='staff_toggle_active'),

    # Attendance
    path('attendance/', views.attendance_list, name='attendance_list'),
    path('attendance/leave/', views.mark_leave, name='mark_leave'),
    path('attendance/export/excel/', views.export_attendance_excel, name='export_attendance_excel'),
    path('attendance/export/pdf/', views.export_attendance_pdf, name='export_attendance_pdf'),

    # Fees
    path('fees/', views.fee_collection, name='fee_collection'),
    path('fees/pay/', views.add_fee_payment, name='add_fee_payment'),
    path('fees/defaulters/', views.fee_defaulters, name='fee_defaulters'),
    path('fees/receipt/<int:pk>/', views.receipt_detail, name='receipt_detail'),
    path('fees/export/excel/', views.export_fees_excel, name='export_fees_excel'),
    path('fees/export/pdf/', views.export_fees_pdf, name='export_fees_pdf'),

    # Accounts (Daily Income/Expenses)
    path('accounts/', views.accounts_list, name='accounts_list'),
    path('accounts/export/excel/', views.export_accounts_excel, name='export_accounts_excel'),
    path('accounts/export/pdf/', views.export_accounts_pdf, name='export_accounts_pdf'),

    # Staff Salary
    path('salary/', views.salary_list, name='salary_list'),
    path('salary/pay/', views.pay_salary, name='pay_salary'),
]
