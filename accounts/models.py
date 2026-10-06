from django.db import models
from django.contrib.auth.models import AbstractUser

class Department(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('STAFF', 'Staff'),
        ('HOD', 'Head of Department'),
        ('ADMIN', 'Admin/Council Manager'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='STAFF')
    account_approved = models.BooleanField(default=False)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True, related_name='employees')

    def __str__(self):
        return f"{self.email} - {self.get_role_display()}"

class ProcurementMemo(models.Model):
    STATUS_CHOICES = (
        ('PENDING_ORIGINATING_HOD', 'Pending Originating HOD Approval'),
        ('PENDING_CM_APPROVAL_1', 'Pending Council Manager Approval (Memo)'),
        ('PENDING_PROCUREMENT', 'Pending Procurement Department'),
        ('PENDING_QUOTES_VOUCHER', 'Pending Quotes & Voucher (Originating Dept)'),
        ('PENDING_CM_APPROVAL_2', 'Pending Council Manager Approval (Voucher)'),
        ('PENDING_BUDGET', 'Pending Budget Department'),
        ('PENDING_AUDIT', 'Pending Audit Department'),
        ('PENDING_PAY_OFFICE', 'Pending Pay Office Release'),
        ('FUNDS_RELEASED_TO_HOD', 'Funds Released to Originating HOD'),
        ('COMPLETED', 'Executed by Contractor'),
        ('REJECTED', 'Rejected/Cancelled'),
    )

    title = models.CharField(max_length=255)
    description = models.TextField()
    amount_requested = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    
    originating_user = models.ForeignKey('CustomUser', on_delete=models.CASCADE, related_name='memos_created')
    originating_department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='department_memos')
    
    current_status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='PENDING_ORIGINATING_HOD')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} - {self.originating_department.name} ({self.get_current_status_display()})"