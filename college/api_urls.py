from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import api_views

router = DefaultRouter()
router.register('students', api_views.StudentViewSet, basename='api-student')
router.register('fees', api_views.FeeTransactionViewSet, basename='api-fee')
router.register('accounts', api_views.AccountTransactionViewSet, basename='api-account')
router.register('salary', api_views.SalaryPaymentViewSet, basename='api-salary')
router.register('staff', api_views.StaffViewSet, basename='api-staff')

urlpatterns = [
    path('auth/login/', api_views.login_api, name='api-login'),
    path('auth/logout/', api_views.logout_api, name='api-logout'),
    path('auth/me/', api_views.me_api, name='api-me'),

    path('dashboard/', api_views.dashboard_api, name='api-dashboard'),

    path('attendance/', api_views.attendance_list_api, name='api-attendance-list'),
    path('attendance/save/', api_views.attendance_save_api, name='api-attendance-save'),
    path('attendance/leaves/', api_views.leaves_api, name='api-leaves'),

    path('fees/defaulters/', api_views.fee_defaulters_api, name='api-fee-defaulters'),

    path('staff/<int:pk>/password/', api_views.staff_set_password_api, name='api-staff-password'),
    path('staff/<int:pk>/toggle/', api_views.staff_toggle_active_api, name='api-staff-toggle'),

    path('', include(router.urls)),
]
