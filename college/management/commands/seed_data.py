from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from college.models import UserProfile, Student, Attendance, FeeTransaction, AccountTransaction, SalaryPayment
from datetime import datetime, timedelta
import random

class Command(BaseCommand):
    help = 'Seeds the database with test data for college management system'

    def handle(self, *args, **options):
        self.stdout.write('Clearing existing database records...')
        Attendance.objects.all().delete()
        FeeTransaction.objects.all().delete()
        AccountTransaction.objects.all().delete()
        SalaryPayment.objects.all().delete()
        Student.objects.all().delete()
        
        # Remove old profiles and users
        UserProfile.objects.all().delete()
        User.objects.all().delete()
        
        self.stdout.write('Creating user profiles (Admin and Staff)...')
        
        # 1. Create Super Admin
        admin_user = User.objects.create_user(
            username='admin',
            email='admin@college.edu',
            password='admin123',
            first_name='Principal',
            last_name='Super Admin'
        )
        UserProfile.objects.create(
            user=admin_user,
            role='ADMIN',
            phone='+919876543210',
            salary=85000.00
        )
        
        # 2. Create Staff Teachers
        staff_1 = User.objects.create_user(
            username='teacher1',
            email='teacher1@college.edu',
            password='teacher123',
            first_name='Rahul',
            last_name='Sharma'
        )
        UserProfile.objects.create(
            user=staff_1,
            role='STAFF',
            phone='+919876543211',
            salary=45000.00
        )

        staff_2 = User.objects.create_user(
            username='teacher2',
            email='teacher2@college.edu',
            password='teacher123',
            first_name='Anjali',
            last_name='Menon'
        )
        UserProfile.objects.create(
            user=staff_2,
            role='STAFF',
            phone='+919876543212',
            salary=48000.00
        )
        
        self.stdout.write('Creating student records...')
        
        # 3. Create Students
        student_data = [
            # BCA Batch 2024-2027
            ('Adarsh', 'Kishore', 'BCA-2024-01', 'ADM-1001', 'BCA', '2024-2027', '+919946001122', 75000.00, 50000.00),
            ('Fathima', 'Sherin', 'BCA-2024-02', 'ADM-1002', 'BCA', '2024-2027', '+919946001123', 75000.00, 75000.00),
            ('Gokul', 'Das', 'BCA-2024-03', 'ADM-1003', 'BCA', '2024-2027', '+919946001124', 75000.00, 30000.00),
            ('Hridya', 'Raj', 'BCA-2024-04', 'ADM-1004', 'BCA', '2024-2027', '+919946001125', 75000.00, 0.00), # Complete Defaulter
            
            # BCom Batch 2024-2027
            ('Abhijith', 'K', 'BCOM-2024-01', 'ADM-2001', 'BCom', '2024-2027', '+919946001126', 60000.00, 60000.00),
            ('Devika', 'Nair', 'BCOM-2024-02', 'ADM-2002', 'BCom', '2024-2027', '+919946001127', 60000.00, 45000.00),
            ('Jithin', 'P', 'BCOM-2024-03', 'ADM-2003', 'BCom', '2024-2027', '+919946001128', 60000.00, 20000.00),
            
            # MCA Batch 2025-2027
            ('Meera', 'Mohan', 'MCA-2025-01', 'ADM-3001', 'MCA', '2025-2027', '+919946001129', 95000.00, 95000.00),
            ('Sanjay', 'V', 'MCA-2025-02', 'ADM-3002', 'MCA', '2025-2027', '+919946001130', 95000.00, 50000.00),
        ]
        
        today = datetime.now().date()
        
        students_list = []
        for first, last, roll, adm, cls_name, batch_name, phone, course_fee, paid_fee in student_data:
            student = Student.objects.create(
                first_name=first,
                last_name=last,
                roll_number=roll,
                admission_number=adm,
                class_name=cls_name,
                batch=batch_name,
                parent_phone=phone,
                total_course_fee=course_fee,
                is_active=True
            )
            students_list.append(student)
            
            # Record fee payments
            if paid_fee > 0:
                payment_date = today - timedelta(days=random.randint(10, 60))
                # Create transactions
                pay_trans = FeeTransaction.objects.create(
                    student=student,
                    amount_paid=paid_fee,
                    payment_date=payment_date,
                    payment_method=random.choice(['CASH', 'BANK']),
                    remarks="Installment Payment"
                )
                # Log matching AccountTransaction Income
                AccountTransaction.objects.create(
                    transaction_type='INCOME',
                    category='Course Fees',
                    amount=paid_fee,
                    date=payment_date,
                    payment_method=pay_trans.payment_method,
                    description=f"Course Fees from {student.full_name} ({student.roll_number}). Receipt: {pay_trans.receipt_number}"
                )

        self.stdout.write('Creating daily accounts logs (Income/Expenses for last 6 months)...')
        
        # 4. Generate Income/Expenses to show nice charts
        categories_expense = ['Rent', 'Electricity Bill', 'Office Supplies', 'Maintenance', 'Internet', 'Marketing']
        
        # Go back 6 months
        for i in range(180, 0, -1):
            log_date = today - timedelta(days=i)
            
            # Monthly rent on 1st of every month
            if log_date.day == 1:
                AccountTransaction.objects.create(
                    transaction_type='EXPENSE',
                    category='Rent',
                    amount=18000.00,
                    date=log_date,
                    payment_method='BANK',
                    description=f"Monthly campus rent for {log_date.strftime('%B %Y')}"
                )
            
            # Monthly electricity bill around 10th
            if log_date.day == 10:
                AccountTransaction.objects.create(
                    transaction_type='EXPENSE',
                    category='Electricity Bill',
                    amount=random.randint(2500, 5000),
                    date=log_date,
                    payment_method='BANK',
                    description="KSEB Electricity Bill"
                )
                
            # Random other minor expenses
            if random.random() < 0.15:  # 15% chance per day
                category = random.choice(categories_expense)
                if category not in ['Rent', 'Electricity Bill']:
                    AccountTransaction.objects.create(
                        transaction_type='EXPENSE',
                        category=category,
                        amount=random.randint(200, 1500),
                        date=log_date,
                        payment_method='CASH',
                        description=f"Purchased {category.lower()} items"
                    )
            
            # Seed extra minor incomes on some days
            if random.random() < 0.05:  # 5% chance
                AccountTransaction.objects.create(
                    transaction_type='INCOME',
                    category='Other Incomes',
                    amount=random.randint(500, 3000),
                    date=log_date,
                    payment_method='CASH',
                    description="Application Forms / Seminar Registration Fees"
                )

        self.stdout.write('Seeding Staff Salaries payroll history...')
        
        # 5. Seed staff salary payments
        months_to_pay = [(today - timedelta(days=30*m)) for m in range(4, 0, -1)]
        for month_date in months_to_pay:
            month_str = month_date.strftime('%Y-%m')
            for teacher in [staff_1, staff_2]:
                basic = teacher.profile.salary
                payment_date = month_date.replace(day=5)  # Paid on 5th of each month
                
                # Pay salary
                payment = SalaryPayment.objects.create(
                    staff=teacher,
                    month=month_str,
                    basic_salary=basic,
                    advance_deducted=0,
                    other_deductions=0,
                    amount_paid=basic,
                    payment_date=payment_date,
                    payment_status='PAID',
                    remarks="Regular Monthly Salary statement cleared"
                )
                # Create Expense log
                AccountTransaction.objects.create(
                    transaction_type='EXPENSE',
                    category='Staff Salary',
                    amount=basic,
                    date=payment_date,
                    payment_method='BANK',
                    description=f"Monthly salary statement paid to {teacher.get_full_name()} ({month_str})"
                )

        self.stdout.write("Logging today's student attendance registry...")
        
        # 6. Seed today and yesterday's attendance
        for date_offset in [0, 1]:
            att_date = today - timedelta(days=date_offset)
            # Skip Sundays
            if att_date.strftime('%w') == '0':
                continue
                
            for student in students_list:
                # Randomize student status for today
                # Student BCA-2024-04 (Hridya) on leave today
                if student.roll_number == 'BCA-2024-04' and date_offset == 0:
                    status = 'LEAVE'
                    reason = "Family function in hometown"
                elif random.random() < 0.88:
                    status = 'PRESENT'
                    reason = ""
                else:
                    status = 'ABSENT'
                    reason = ""
                    
                Attendance.objects.create(
                    student=student,
                    date=att_date,
                    period='Daily',
                    status=status,
                    marked_by=admin_user,
                    leave_reason=reason
                )

        self.stdout.write(self.style.SUCCESS('Successfully seeded database with college records!'))
        self.stdout.write(self.style.SUCCESS('Login credentials:'))
        self.stdout.write(self.style.SUCCESS('  Super Admin (MD): username: admin  | password: admin123'))
        self.stdout.write(self.style.SUCCESS('  Staff/Teacher:   username: teacher1 | password: teacher123'))
