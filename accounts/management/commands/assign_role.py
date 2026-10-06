from django.core.management.base import BaseCommand
from accounts.models import User, Department

class Command(BaseCommand):
    help = 'Assign a role (STAFF, HOD, ADMIN) and department to a user, and ensure account is approved and verified.'

    def add_arguments(self, parser):
        parser.add_argument('--email', type=str, help='Email of the user')
        parser.add_argument('--role', type=str, choices=['STAFF', 'HOD', 'ADMIN'], default='HOD', help='Role to assign')
        parser.add_argument('--dept', type=str, help='Name of the department')
        parser.add_argument('--list', action='store_true', help='List all users, departments, and roles')

    def handle(self, *args, **options):
        if options['list']:
            self.stdout.write(self.style.SUCCESS("Current Users:"))
            for u in User.objects.all():
                dept_name = u.department.name if u.department else "None"
                self.stdout.write(f" - {u.email} | Role: {u.role} | Dept: {dept_name} | Verified: {u.email_verified} | Approved: {u.account_approved}")
            return

        email = options.get('email')
        if not email:
            self.stdout.write(self.style.ERROR("Please provide an --email or use --list."))
            return

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"User with email '{email}' does not exist."))
            return

        role = options.get('role')
        dept_name = options.get('dept')

        user.role = role
        user.email_verified = True
        user.account_approved = True

        if dept_name:
            dept, _ = Department.objects.get_or_create(name=dept_name)
            user.department = dept

        user.save()
        self.stdout.write(self.style.SUCCESS(f"Successfully updated {user.email}: Role={user.role}, Dept={user.department}"))
