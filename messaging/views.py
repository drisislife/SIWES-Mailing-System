from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import get_user_model
from .models import Message
from .forms import MessageForm

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
    """All messages delivered to this user."""
    received = Message.objects.filter(
        recipient=request.user,
        status='approved'
    ).order_by('-timestamp')

    unread_count = received.filter(is_read=False).count()

    return render(request, 'messaging/inbox.html', {
        'memos': received,
        'received_messages': received,
        'unread_count': unread_count,
    })


# ---------------------------------------------------------------------------
# Sent
# ---------------------------------------------------------------------------

@login_required
def sent_view(request):
    """All messages sent by this user."""
    sent = Message.objects.filter(sender=request.user).order_by('-timestamp')
    return render(request, 'messaging/sent.html', {
        'memos': sent,
        'sent_messages': sent,
    })


# ---------------------------------------------------------------------------
# Compose
# ---------------------------------------------------------------------------

@login_required
def compose_view(request):
    """
    Compose a new memo.
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
        form = MessageForm(request.POST)
        if form.is_valid():
            memo = form.save(commit=False)
            memo.sender = request.user

            sender_dept = getattr(request.user, 'department', None)
            recipient_dept = getattr(memo.recipient, 'department', None)

            if sender_dept and recipient_dept and sender_dept == recipient_dept:
                memo.status = 'approved'
                messages.success(request, f'Memo sent to {memo.recipient.get_full_name() or memo.recipient.email}.')
            else:
                memo.status = 'pending_hod'
                messages.info(request, 'Memo submitted for HOD approval (cross-department).')

            memo.save()
            return redirect('sent_messages')
    else:
        initial = {}
        recipient_id = request.GET.get('recipient')
        subject = request.GET.get('subject')
        if recipient_id:
            try:
                initial['recipient'] = int(recipient_id)
            except ValueError:
                pass
        if subject:
            initial['subject'] = subject

        form = MessageForm(initial=initial)

    return render(request, 'messaging/compose.html', {'form': form})


# ---------------------------------------------------------------------------
# Message detail
# ---------------------------------------------------------------------------

@login_required
def message_detail_view(request, pk):
    """View a single message; mark it as read if recipient is viewing."""
    memo = get_object_or_404(Message, pk=pk)

    # Permission check: sender, recipient, or admin/hod
    if request.user not in (memo.sender, memo.recipient) and not request.user.is_superuser and not _is_hod(request.user):
        messages.error(request, 'You do not have permission to view this memo.')
        return redirect('inbox')

    is_recipient = (request.user == memo.recipient)
    if is_recipient and not memo.is_read:
        memo.is_read = True
        memo.save(update_fields=['is_read'])

    sender_dept_id = getattr(memo.sender, 'department_id', None)
    recipient_dept_id = getattr(memo.recipient, 'department_id', None)
    is_cross_department = (sender_dept_id != recipient_dept_id)

    return render(request, 'messaging/message_detail.html', {
        'memo': memo,
        'message': memo,
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