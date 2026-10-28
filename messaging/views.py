from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.db.models import Q
from .models import Message, MessageMinute, CouncilCircular
from .forms import MessageForm, MessageMinuteForm, CouncilCircularForm

User = get_user_model()


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _is_hod(user):
    return getattr(user, 'role', '') in ('HOD', 'ADMIN') or user.is_superuser


# ---------------------------------------------------------------------------
# Inbox
# ---------------------------------------------------------------------------

@login_required
def inbox_view(request):
    """All messages delivered to this user with search & priority filtering."""
    received = Message.objects.filter(
        recipient=request.user,
        status='approved'
    ).select_related('sender', 'recipient', 'sender__department', 'recipient__department').order_by('-timestamp')

    q = request.GET.get('q', '').strip()
    priority = request.GET.get('priority', '').strip()

    if q:
        received = received.filter(
            Q(subject__icontains=q) |
            Q(body__icontains=q) |
            Q(ref_number__icontains=q) |
            Q(sender__first_name__icontains=q) |
            Q(sender__last_name__icontains=q) |
            Q(sender__email__icontains=q) |
            Q(sender__department__name__icontains=q)
        )

    if priority:
        received = received.filter(priority=priority)

    unread_count = received.filter(is_read=False).count()

    return render(request, 'messaging/inbox.html', {
        'memos': received,
        'received_messages': received,
        'unread_count': unread_count,
        'search_query': q,
        'selected_priority': priority,
    })


# ---------------------------------------------------------------------------
# Sent
# ---------------------------------------------------------------------------

@login_required
def sent_view(request):
    """All messages sent by this user with search & priority filtering."""
    sent = Message.objects.filter(sender=request.user).select_related('recipient', 'recipient__department').order_by('-timestamp')

    q = request.GET.get('q', '').strip()
    priority = request.GET.get('priority', '').strip()

    if q:
        sent = sent.filter(
            Q(subject__icontains=q) |
            Q(body__icontains=q) |
            Q(ref_number__icontains=q) |
            Q(recipient__first_name__icontains=q) |
            Q(recipient__last_name__icontains=q) |
            Q(recipient__email__icontains=q) |
            Q(recipient__department__name__icontains=q)
        )

    if priority:
        sent = sent.filter(priority=priority)

    return render(request, 'messaging/sent.html', {
        'memos': sent,
        'sent_messages': sent,
        'search_query': q,
        'selected_priority': priority,
    })


# ---------------------------------------------------------------------------
# Compose
# ---------------------------------------------------------------------------

@login_required
def compose_view(request):
    """
    Compose a new memo with priority, file attachment, and auto reference numbering.
    • Same department → instantly 'approved' (delivered).
    • Different department → 'pending_hod' (HOD of the sender's dept must approve).
    • Unverified accounts cannot compose or dispatch memos.
    """
    if not getattr(request.user, 'account_approved', False) and not request.user.is_superuser:
        messages.warning(
            request,
            'Your account is pending Administrator verification. You cannot compose or send messages until an administrator has verified your account.'
        )
        return redirect('dashboard')

    if request.method == 'POST':
        form = MessageForm(request.POST, request.FILES)
        if form.is_valid():
            memo = form.save(commit=False)
            memo.sender = request.user

            sender_dept = getattr(request.user, 'department', None)
            recipient_dept = getattr(memo.recipient, 'department', None)

            if sender_dept and recipient_dept and sender_dept == recipient_dept:
                memo.status = 'approved'
                messages.success(request, f'Official memo dispatched successfully to {memo.recipient.get_full_name()}.')
            else:
                memo.status = 'pending_hod'
                messages.info(request, 'Cross-department memo forwarded to your Head of Department (HOD) for review & endorsement.')

            memo.save()
            return redirect('sent_messages')
    else:
        initial = {}
        recipient_id = request.GET.get('recipient')
        subject = request.GET.get('subject')
        priority = request.GET.get('priority')
        if recipient_id:
            try:
                initial['recipient'] = int(recipient_id)
            except ValueError:
                pass
        if subject:
            initial['subject'] = subject
        if priority:
            initial['priority'] = priority

        form = MessageForm(initial=initial)

    return render(request, 'messaging/compose.html', {'form': form})


# ---------------------------------------------------------------------------
# Message detail
# ---------------------------------------------------------------------------

@login_required
def message_detail_view(request, pk):
    """View a single message; mark it as read if recipient is viewing; view and add official minutes."""
    memo = get_object_or_404(Message, pk=pk)

    # Permission check: sender, recipient, or admin/hod
    if request.user not in (memo.sender, memo.recipient) and not request.user.is_superuser and not _is_hod(request.user):
        messages.error(request, 'You do not have permission to view this memo.')
        return redirect('inbox')

    is_recipient = (request.user == memo.recipient)
    if is_recipient and not memo.is_read:
        memo.is_read = True
        memo.save(update_fields=['is_read'])

    minute_form = MessageMinuteForm()
    if request.method == 'POST' and request.POST.get('action') == 'add_minute':
        if not getattr(request.user, 'account_approved', False) and not request.user.is_superuser:
            messages.warning(request, 'Unverified accounts cannot add official minutes.')
        else:
            minute_form = MessageMinuteForm(request.POST)
            if minute_form.is_valid():
                minute = minute_form.save(commit=False)
                minute.message = memo
                minute.officer = request.user
                minute.save()
                messages.success(request, 'Official minute recorded successfully.')
                return redirect('message_detail', pk=pk)

    minutes = memo.minutes.select_related('officer', 'officer__department').all()

    sender_dept_id = getattr(memo.sender, 'department_id', None)
    recipient_dept_id = getattr(memo.recipient, 'department_id', None)
    is_cross_department = (sender_dept_id != recipient_dept_id)

    return render(request, 'messaging/message_detail.html', {
        'memo': memo,
        'message': memo,
        'minutes': minutes,
        'minute_form': minute_form,
        'is_recipient': is_recipient,
        'is_cross_department': is_cross_department,
    })


# ---------------------------------------------------------------------------
# Toggle Read / Unread
# ---------------------------------------------------------------------------

@login_required
def toggle_message_read_view(request, pk):
    """Toggle read/unread status for the recipient."""
    memo = get_object_or_404(Message, pk=pk)
    if request.user == memo.recipient:
        memo.is_read = not memo.is_read
        memo.save(update_fields=['is_read'])
        state = 'read' if memo.is_read else 'unread'
        messages.success(request, f'Message marked as {state}.')
    return redirect('message_detail', pk=pk)


# ---------------------------------------------------------------------------
# HOD approval queue
# ---------------------------------------------------------------------------

@login_required
def hod_approvals_view(request):
    """HOD sees all cross-department memos awaiting their approval."""
    if not _is_hod(request.user):
        messages.error(request, 'Only HODs can access the approval queue.')
        return redirect('inbox')

    hod_dept = getattr(request.user, 'department', None)

    if request.user.is_superuser or getattr(request.user, 'role', '') == 'ADMIN':
        pending = Message.objects.filter(status='pending_hod').order_by('-timestamp')
        processed = Message.objects.filter(status__in=['approved', 'rejected']).order_by('-timestamp')[:10]
    else:
        if hod_dept is None:
            messages.warning(request, 'You are not assigned to a department.')
            return redirect('inbox')

        pending = Message.objects.filter(
            sender__department=hod_dept,
            status='pending_hod'
        ).order_by('-timestamp')

        processed = Message.objects.filter(
            sender__department=hod_dept,
            status__in=['approved', 'rejected']
        ).order_by('-timestamp')[:10]

    return render(request, 'messaging/hod_approvals.html', {
        'pending_memos': pending,
        'pending_messages': pending,
        'processed_memos': processed,
        'processed_messages': processed,
        'is_admin': request.user.is_superuser or getattr(request.user, 'role', '') == 'ADMIN',
    })


# ---------------------------------------------------------------------------
# HOD review a single memo
# ---------------------------------------------------------------------------

@login_required
def hod_review_view(request, pk):
    """HOD approves or rejects (with optional edit) a pending memo."""
    if not _is_hod(request.user):
        messages.error(request, 'Only HODs can review memos.')
        return redirect('inbox')

    memo = get_object_or_404(Message, pk=pk, status='pending_hod')
    hod_dept = getattr(request.user, 'department', None)

    if not (request.user.is_superuser or getattr(request.user, 'role', '') == 'ADMIN'):
        if memo.sender.department != hod_dept:
            messages.error(request, 'This memo does not belong to your department.')
            return redirect('hod_approvals')

    if request.method == 'POST':
        action = request.POST.get('action')
        comment = request.POST.get('hod_comment', '').strip()
        edited_body = request.POST.get('body', '').strip()

        if action == 'approve':
            if edited_body and edited_body != memo.body:
                memo.original_body = memo.body
                memo.body = edited_body
                memo.edited_by_hod = True
            memo.hod_comment = comment
            memo.status = 'approved'
            messages.success(request, f'Memo "{memo.subject}" approved and delivered.')

        elif action == 'reject':
            memo.hod_comment = comment
            memo.status = 'rejected'
            messages.warning(request, f'Memo "{memo.subject}" rejected.')

        memo.save()
        return redirect('hod_approvals')

    return render(request, 'messaging/hod_review_message.html', {
        'memo': memo,
        'message': memo,
    })


# ---------------------------------------------------------------------------
# Delete a message
# ---------------------------------------------------------------------------

@login_required
def delete_message_view(request, pk):
    """Allow sender or recipient to delete."""
    memo = get_object_or_404(Message, pk=pk)

    if request.user not in (memo.sender, memo.recipient) and not request.user.is_superuser:
        messages.error(request, 'You cannot delete this memo.')
        return redirect('inbox')

    next_url = request.POST.get('next') or request.GET.get('next')

    if request.method == 'POST':
        memo.delete()
        messages.success(request, 'Memo deleted.')
        if next_url:
            return redirect(next_url)
        return redirect('inbox')

    return render(request, 'messaging/message_detail.html', {
        'memo': memo,
        'message': memo,
        'confirm_delete': True,
    })


# ---------------------------------------------------------------------------
# Council Circulars & Announcements
# ---------------------------------------------------------------------------

@login_required
def circulars_list_view(request):
    """All active council circulars & announcements."""
    circulars = CouncilCircular.objects.filter(is_active=True).select_related('published_by', 'published_by__department')
    return render(request, 'messaging/circulars_list.html', {
        'circulars': circulars,
        'can_publish': _is_hod(request.user),
    })


@login_required
def create_circular_view(request):
    """Publish a new council circular (HOD / Admin only)."""
    if not _is_hod(request.user):
        messages.error(request, 'Permission Denied: Only Department Heads or Council Administrators can issue council circulars.')
        return redirect('circulars_list')

    if request.method == 'POST':
        form = CouncilCircularForm(request.POST, request.FILES)
        if form.is_valid():
            circ = form.save(commit=False)
            circ.published_by = request.user
            circ.save()
            messages.success(request, f'Official Circular "{circ.title}" published to all personnel.')
            return redirect('circulars_list')
    else:
        form = CouncilCircularForm()

    return render(request, 'messaging/circular_create.html', {'form': form})
