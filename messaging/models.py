import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone


class Message(models.Model):
    STATUS_CHOICES = (
        ('pending_hod', 'Pending HOD Approval'),
        ('approved', 'Delivered'),
        ('rejected', 'Rejected by HOD'),
        ('recalled', 'Recalled by Sender'),
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

    # Recall tracking (Feature 5)
    recalled_at = models.DateTimeField(null=True, blank=True)
    recall_reason = models.CharField(max_length=255, blank=True, default='', help_text="Reason for recalling memo")

    # Priority Escalation (Feature 19)
    escalated = models.BooleanField(default=False)
    escalated_at = models.DateTimeField(null=True, blank=True)

    # Reply threading
    parent = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='replies',
        help_text="Parent memorandum in reply chain"
    )

    # Timestamps & Tracking
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True, help_text="Timestamp when recipient first opened the memo")
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


class MessageAcknowledgement(models.Model):
    """Formal sign-off and receipt acknowledgement for official council memos."""
    message = models.OneToOneField(Message, on_delete=models.CASCADE, related_name='acknowledgement')
    acknowledged_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='acknowledgements')
    acknowledged_at = models.DateTimeField(auto_now_add=True)
    note = models.CharField(max_length=255, blank=True, default='', help_text="Optional brief acknowledgement note")

    class Meta:
        ordering = ['-acknowledged_at']

    def __str__(self):
        return f"Acknowledged by {self.acknowledged_by} on {self.message.ref_number} at {self.acknowledged_at}"


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


class MemoTemplate(models.Model):
    """Pre-formatted standard council memorandum templates (Feature 9)."""
    title = models.CharField(max_length=150)
    category = models.CharField(max_length=100, default='General Administration')
    default_priority = models.CharField(max_length=20, choices=Message.PRIORITY_CHOICES, default='ROUTINE')
    default_subject = models.CharField(max_length=255)
    default_body = models.TextField()
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    is_system_template = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['category', 'title']

    def __str__(self):
        return f"{self.title} ({self.category})"


class Notification(models.Model):
    """In-app alert for user actions, memo routing, and circulars (Feature 10)."""
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    verb = models.CharField(max_length=255)
    target_url = models.CharField(max_length=255, blank=True, default='')
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Notification for {self.recipient}: {self.verb}"


class NoticeBoardItem(models.Model):
    """Internal Council Notice Board for informal announcements and events (Feature 17)."""
    CATEGORY_CHOICES = (
        ('GENERAL', 'General Notice'),
        ('MEETING', 'Council / Dept Meeting'),
        ('WELFARE', 'Staff Welfare & Events'),
        ('URGENT', 'Urgent Council Advisory'),
    )

    title = models.CharField(max_length=255)
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES, default='GENERAL')
    content = models.TextField()
    is_pinned = models.BooleanField(default=False, help_text="Pin to top of notice board")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notices_posted')
    attachment = models.FileField(upload_to='notice_board/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_pinned', '-created_at']

    def __str__(self):
        return f"[{self.get_category_display()}] {self.title}"
