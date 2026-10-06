from django.db import models
from django.conf import settings


class Message(models.Model):
    STATUS_CHOICES = (
        ('pending_hod', 'Pending HOD Approval'),
        ('approved', 'Delivered'),
        ('rejected', 'Rejected by HOD'),
    )

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

    def __str__(self):
        return f"{self.subject} | {self.sender} → {self.recipient} [{self.status}]"