from django.contrib import admin
from .models import Message


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('subject', 'sender', 'recipient', 'status', 'is_read', 'edited_by_hod', 'timestamp')
    list_filter = ('status', 'is_read', 'edited_by_hod')
    search_fields = ('subject', 'sender__email', 'recipient__email')