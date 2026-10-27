from django.db import models
from django.contrib.auth.models import AbstractUser

class Department(models.Model):
    CODE_CHOICES = (
        ('LINE', 'General / Originating Department (ICT, WAPA, Tourism, etc.)'),
        ('CM', "Council Manager's Office"),
        ('PROCUREMENT', 'Procurement Department'),
        ('BUDGET', 'Budget Department'),
        ('AUDIT', 'Internal Audit Office'),
        ('PAY_OFFICE', 'Pay Office / Treasury'),
    )

    name = models.CharField(max_length=150, unique=True)
    code = models.CharField(max_length=20, choices=CODE_CHOICES, default='LINE')
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.name} ({self.get_code_display()})"

class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('STAFF', 'Staff'),
        ('HOD', 'Head of Department'),
        ('ADMIN', 'Admin/Council Manager'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='STAFF')
    position = models.CharField(max_length=150, blank=True, default='', help_text="Official designation or job title")
    account_approved = models.BooleanField(default=False)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True, related_name='employees')

    def get_full_name(self):
        full = f"{self.first_name} {self.last_name}".strip()
        return full if full else (self.username or self.email)

    def __str__(self):
        name = self.get_full_name()
        return f"{name} ({self.email}) - {self.get_role_display()}"

class ProcurementMemo(models.Model):
    STATUS_CHOICES = (
        ('PENDING_ORIGINATING_HOD', 'Step 1: Pending Originating HOD Approval'),
        ('PENDING_CM_APPROVAL_1', 'Step 2: Pending Council Manager Approval (Memo)'),
        ('PENDING_PROCUREMENT', 'Step 3: Pending Procurement Department'),
        ('PENDING_QUOTES_VOUCHER', 'Step 4: Pending Quotes & Voucher (Originating Dept)'),
        ('PENDING_CM_APPROVAL_2', 'Step 5: Pending Council Manager Approval (Voucher)'),
        ('PENDING_BUDGET', 'Step 6: Pending Budget Department Verification'),
        ('PENDING_AUDIT', 'Step 7: Pending Internal Audit Office'),
        ('PENDING_PAY_OFFICE', 'Step 8: Pending Pay Office / Treasury Release'),
        ('FUNDS_RELEASED_TO_HOD', 'Step 9: Funds Released to Originating HOD'),
        ('COMPLETED', 'Step 10: Contract Executed & Completed'),
        ('REJECTED', 'Rejected / Returned'),
    )

    title = models.CharField(max_length=255)
    description = models.TextField()
    estimated_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, help_text="Initial estimated cost")
    final_voucher_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, help_text="Calculated voucher amount")
    voucher_number = models.CharField(max_length=100, blank=True, null=True, help_text="Official voucher reference code")

    # Document Uploads for quotations, vouchers, and attachments
    memo_document = models.FileField(upload_to='procurement/memos/', null=True, blank=True)
    quotations_document = models.FileField(upload_to='procurement/quotations/', null=True, blank=True, help_text="Quotations from vendors")
    voucher_document = models.FileField(upload_to='procurement/vouchers/', null=True, blank=True, help_text="Prepared payment voucher")

    # Dynamic Ownership: Tracks the originating line department (ICT, WAPA, Tourism, etc.)
    originating_user = models.ForeignKey('CustomUser', on_delete=models.CASCADE, related_name='memos_created')
    originating_department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='department_memos')

    current_status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='PENDING_ORIGINATING_HOD')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} - {self.originating_department.name} [{self.get_current_status_display()}]"


class ProcurementActionLog(models.Model):
    """Audit log recording every approval, sign-off, comment, and rejection along the track."""
    memo = models.ForeignKey(ProcurementMemo, on_delete=models.CASCADE, related_name='action_logs')
    actor = models.ForeignKey('CustomUser', on_delete=models.SET_NULL, null=True)
    actor_department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=100)  # e.g. "APPROVED_BY_HOD", "QUOTES_ATTACHED", "PAYMENT_RELEASED", "REJECTED"
    stage = models.CharField(max_length=50)
    comments = models.TextField(blank=True, default='')
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.memo.title} - {self.action} by {self.actor} at {self.timestamp}"