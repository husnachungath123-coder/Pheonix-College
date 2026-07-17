from django.contrib import admin
from .models import UserProfile, Student, Attendance, FeeTransaction, AccountTransaction, SalaryPayment

admin.site.register(UserProfile)
admin.site.register(Student)
admin.site.register(Attendance)
admin.site.register(FeeTransaction)
admin.site.register(AccountTransaction)
admin.site.register(SalaryPayment)
