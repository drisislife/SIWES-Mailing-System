from django.contrib import admin
from .models import Message, MessageMinute, CouncilCircular, MessageAcknowledgement, MemoTemplate, Notification, NoticeBoardItem


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('ref_number', 'subject', 'sender', 'recipient', 'status', 'is_read', 'read_at', 'timestamp')
    list_filter = ('status', 'is_read', 'priority')
    search_fields = ('ref_number', 'subject', 'sender__email', 'recipient__email')


@admin.register(MessageMinute)
class MessageMinuteAdmin(admin.ModelAdmin):
    list_display = ('message', 'officer', 'created_at')
    search_fields = ('message__ref_number', 'officer__email', 'comment')


@admin.register(MessageAcknowledgement)
class MessageAcknowledgementAdmin(admin.ModelAdmin):
    list_display = ('message', 'acknowledged_by', 'acknowledged_at', 'note')
    search_fields = ('message__ref_number', 'acknowledged_by__email', 'note')


@admin.register(CouncilCircular)
class CouncilCircularAdmin(admin.ModelAdmin):
    list_display = ('title', 'priority', 'published_by', 'is_active', 'created_at')
    list_filter = ('priority', 'is_active')
    search_fields = ('title', 'content')


@admin.register(MemoTemplate)
class MemoTemplateAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'default_priority', 'is_system_template', 'created_at')
    list_filter = ('category', 'default_priority', 'is_system_template')
    search_fields = ('title', 'default_subject', 'default_body')


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('recipient', 'actor', 'verb', 'is_read', 'created_at')
    list_filter = ('is_read',)
    search_fields = ('recipient__email', 'verb')


@admin.register(NoticeBoardItem)
class NoticeBoardItemAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'author', 'is_pinned', 'created_at')
    list_filter = ('category', 'is_pinned')
    search_fields = ('title', 'content', 'author__email')
