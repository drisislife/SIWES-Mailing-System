import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone


class Message(models.Model):
    STATUS_CHOICES = (
        ('pending_hod', 'Pending HOD Approval'),
        ('approved', 'Delivered'),
        ('rejected', 'Rejected by HOD'),
    )

    PRIORITY_CHOICES = (
        ('ROUTINE', 'Routine'),
        ('URGENT', 'Urgent'),
        ('CONFIDENTIAL', 'Confidential'),
    )

    ref_number = models.CharField(max_length=100, blank=True, unique=True, null=True, help_text="Official Reference Number")
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='ROUTINE')
    attachment = models.FileField(upload_to='messaging/attachments/', blank=True, null=True, help_text="Attach official documents, scans, or PDFs")

    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_messages'
    )
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='received_messages'
    )

    subject = models.CharField(max_length=255)
    body = models.TextField()

    # HOD workflow fields
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='approved')
    hod_comment = models.TextField(blank=True, default='')
    edited_by_hod = models.BooleanField(default=False)
    original_body = models.TextField(blank=True, default='')

    # Timestamps & Tracking
    is_read = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)  # views order by -timestamp

    def save(self, *args, **kwargs):
        if not self.ref_number:
            year = timezone.now().year
            dept_code = 'GEN'
            if hasattr(self.sender, 'department') and self.sender.department:
                dept_code = getattr(self.sender.department, 'code', '') or self.sender.department.name[:4].upper()
            rand_id = uuid.uuid4().hex[:5].upper()
            self.ref_number = f"CWS/{dept_code}/{year}/{rand_id}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"[{self.ref_number or 'MEMO'}] {self.subject} | {self.sender} → {self.recipient} [{self.status}]"


class MessageMinute(models.Model):
    """Internal Minutes / Endorsements / Annotations added to official memos."""
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='minutes')
    officer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='minutes_given')
    comment = models.TextField(help_text="Official minute or notation")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Minute by {self.officer} on {self.message.ref_number}"


class CouncilCircular(models.Model):
    """Official Broadcast / Circular published by Council Administration."""
    PRIORITY_CHOICES = (
        ('NORMAL', 'General Circular'),
        ('IMPORTANT', 'Important Notice'),
        ('URGENT', 'Urgent Directive'),
    )

    title = models.CharField(max_length=255)
    content = models.TextField()
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='NORMAL')
    attachment = models.FileField(upload_to='circulars/', blank=True, null=True)
    published_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='circulars_published')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} ({self.get_priority_display()})"
