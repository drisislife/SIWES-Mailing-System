import csv
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.db.models import Q, Count
from django.utils import timezone
from django.http import JsonResponse, HttpResponse
from .models import (
    Message, MessageMinute, CouncilCircular, MessageAcknowledgement,
    MemoTemplate, Notification, NoticeBoardItem
)
from .forms import (
    MessageForm, MessageMinuteForm, CouncilCircularForm,
    MessageAcknowledgementForm, NoticeBoardForm, MemoRecallForm
)
from accounts.audit import log_audit
from .notifications import send_notification

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
    ).select_related('sender', 'recipient', 'sender__department', 'recipient__department', 'acknowledgement', 'parent').order_by('-timestamp')

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
    sent = Message.objects.filter(sender=request.user).select_related('recipient', 'recipient__department', 'acknowledgement', 'parent').order_by('-timestamp')

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
    • Supports reply chaining (?parent=<id>).
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

    parent_id = request.POST.get('parent') or request.GET.get('parent')
    parent_memo = None
    if parent_id:
        parent_memo = Message.objects.filter(pk=parent_id).select_related('sender', 'recipient', 'sender__department').first()

    if request.method == 'POST':
        form = MessageForm(request.POST, request.FILES)
        if form.is_valid():
            memo = form.save(commit=False)
            memo.sender = request.user
            if parent_memo:
                memo.parent = parent_memo

            sender_dept = getattr(request.user, 'department', None)
            recipient_dept = getattr(memo.recipient, 'department', None)

            if sender_dept and recipient_dept and sender_dept == recipient_dept:
                memo.status = 'approved'
                messages.success(request, f'Official memo dispatched successfully to {memo.recipient.get_full_name()}.')
            else:
                memo.status = 'pending_hod'
                messages.info(request, 'Cross-department memo forwarded to your Head of Department (HOD) for review & endorsement.')

            memo.save()

            log_audit(request, 'MEMO_SENT', f"Dispatched memo {memo.ref_number} to {memo.recipient.email} [{memo.status}]")

            if memo.status == 'approved':
                send_notification(
                    recipient=memo.recipient,
                    verb=f"New memorandum received: {memo.subject}",
                    target_url=f"/messaging/{memo.id}/",
                    actor=request.user
                )
            elif memo.status == 'pending_hod' and sender_dept:
                hod_user = User.objects.filter(department=sender_dept, role='HOD', account_approved=True).first()
                if hod_user:
                    send_notification(
                        recipient=hod_user,
                        verb=f"Cross-department memo awaiting your review: {memo.subject}",
                        target_url="/messaging/hod/approvals/",
                        actor=request.user
                    )

            return redirect('sent_messages')
    else:
        initial = {}
        recipient_id = request.GET.get('recipient')
        subject = request.GET.get('subject')
        priority = request.GET.get('priority')

        if not recipient_id and parent_memo:
            if parent_memo.recipient == request.user:
                initial['recipient'] = parent_memo.sender_id
            elif parent_memo.sender == request.user:
                initial['recipient'] = parent_memo.recipient_id
        elif recipient_id:
            try:
                initial['recipient'] = int(recipient_id)
            except ValueError:
                pass

        if not subject and parent_memo:
            clean_sub = parent_memo.subject.replace('Re: ', '').replace('RE: ', '')
            initial['subject'] = f"Re: {clean_sub}"
        elif subject:
            initial['subject'] = subject

        if not priority and parent_memo:
            initial['priority'] = parent_memo.priority
        elif priority:
            initial['priority'] = priority

        template_id = request.GET.get('template')
        if template_id:
            tmpl = MemoTemplate.objects.filter(pk=template_id).first()
            if tmpl:
                initial['subject'] = tmpl.default_subject
                initial['body'] = tmpl.default_body
                initial['priority'] = tmpl.default_priority

        form = MessageForm(initial=initial)

    templates = MemoTemplate.objects.all().order_by('category', 'title')

    return render(request, 'messaging/compose.html', {
        'form': form,
        'parent_memo': parent_memo,
        'templates': templates,
    })


# ---------------------------------------------------------------------------
# Message detail
# ---------------------------------------------------------------------------

@login_required
def message_detail_view(request, pk):
    """View a single message; mark it as read & record read receipt; view and add official minutes; acknowledge receipt; view reply thread."""
    memo = get_object_or_404(Message.objects.select_related(
        'sender', 'recipient', 'sender__department', 'recipient__department', 'parent'
    ), pk=pk)

    # Permission check: sender, recipient, or admin/hod
    if request.user not in (memo.sender, memo.recipient) and not request.user.is_superuser and not _is_hod(request.user):
        messages.error(request, 'You do not have permission to view this memo.')
        return redirect('inbox')

    # Priority Escalation (Feature 19)
    if memo.priority in ('URGENT', 'CONFIDENTIAL') and not memo.is_read:
        if (timezone.now() - memo.timestamp).total_seconds() > 86400 and not memo.escalated:
            memo.escalated = True
            memo.escalated_at = timezone.now()
            memo.save(update_fields=['escalated', 'escalated_at'])

    is_recipient = (request.user == memo.recipient)
    if is_recipient:
        updated = False
        if not memo.is_read:
            memo.is_read = True
            updated = True
        if not memo.read_at:
            memo.read_at = timezone.now()
            updated = True
            log_audit(request, 'MEMO_READ', f"Memo {memo.ref_number} opened by {request.user.email}")
        if updated:
            memo.save(update_fields=['is_read', 'read_at'])

    minute_form = MessageMinuteForm()
    ack_form = MessageAcknowledgementForm()

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'add_minute':
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
        elif action == 'acknowledge':
            if not is_recipient:
                messages.error(request, 'Only the addressed officer can formally acknowledge receipt.')
            elif memo.status != 'approved':
                messages.warning(request, 'Only delivered memorandums can be acknowledged.')
            elif hasattr(memo, 'acknowledgement'):
                messages.info(request, 'This memorandum has already been officially acknowledged.')
            else:
                ack_form = MessageAcknowledgementForm(request.POST)
                if ack_form.is_valid():
                    ack = ack_form.save(commit=False)
                    ack.message = memo
                    ack.acknowledged_by = request.user
                    ack.save()
                    log_audit(request, 'MEMO_ACKNOWLEDGED', f"Memo {memo.ref_number} receipt signed off by {request.user.email}")
                    send_notification(
                        recipient=memo.sender,
                        verb=f"Receipt of memo {memo.ref_number} was officially signed off by {request.user.get_full_name()}.",
                        target_url=f"/messaging/{memo.id}/",
                        actor=request.user
                    )
                    messages.success(request, f'Receipt of memorandum {memo.ref_number} successfully acknowledged.')
                    return redirect('message_detail', pk=pk)

    minutes = memo.minutes.select_related('officer', 'officer__department').all()
    acknowledgement = getattr(memo, 'acknowledgement', None)
    parent_memo = memo.parent
    replies = memo.replies.select_related('sender', 'recipient', 'sender__department').order_by('timestamp')

    sender_dept_id = getattr(memo.sender, 'department_id', None)
    recipient_dept_id = getattr(memo.recipient, 'department_id', None)
    is_cross_department = (sender_dept_id != recipient_dept_id)

    return render(request, 'messaging/message_detail.html', {
        'memo': memo,
        'message': memo,
        'minutes': minutes,
        'minute_form': minute_form,
        'ack_form': ack_form,
        'acknowledgement': acknowledgement,
        'parent_memo': parent_memo,
        'replies': replies,
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
        if memo.is_read and not memo.read_at:
            memo.read_at = timezone.now()
        elif not memo.is_read:
            memo.read_at = None
        memo.save(update_fields=['is_read', 'read_at'])
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


# ---------------------------------------------------------------------------
# Memo Recall / Withdraw (Feature 5)
# ---------------------------------------------------------------------------

@login_required
def memo_recall_view(request, pk):
    """Allow originating officer to recall/withdraw an unread memo."""
    memo = get_object_or_404(Message, pk=pk)

    if request.user != memo.sender and not request.user.is_superuser:
        messages.error(request, 'Permission Denied: Only the originating officer can recall this memorandum.')
        return redirect('message_detail', pk=pk)

    if memo.is_read:
        messages.warning(request, 'Action Prohibited: This memorandum has already been opened by the recipient and cannot be recalled.')
        return redirect('message_detail', pk=pk)

    if memo.status == 'recalled':
        messages.info(request, 'This memorandum has already been recalled.')
        return redirect('message_detail', pk=pk)

    if request.method == 'POST':
        form = MemoRecallForm(request.POST)
        if form.is_valid():
            reason = form.cleaned_data['recall_reason']
            memo.status = 'recalled'
            memo.recalled_at = timezone.now()
            memo.recall_reason = reason
            memo.save(update_fields=['status', 'recalled_at', 'recall_reason'])

            log_audit(request, 'MEMO_RECALLED', f"Recalled memo {memo.ref_number}. Reason: {reason}")
            send_notification(
                recipient=memo.recipient,
                verb=f"Memorandum {memo.ref_number} was withdrawn/recalled by sender ({request.user.get_full_name()}).",
                target_url=f"/messaging/{memo.id}/",
                actor=request.user
            )
            messages.success(request, f'Memorandum {memo.ref_number} has been officially withdrawn and recalled.')
            return redirect('sent_messages')
    else:
        form = MemoRecallForm()

    return render(request, 'messaging/memo_recall.html', {
        'memo': memo,
        'form': form,
    })


# ---------------------------------------------------------------------------
# Official Memo PDF / Printable Letterhead (Feature 12)
# ---------------------------------------------------------------------------

@login_required
def memo_pdf_view(request, pk):
    """High-fidelity official council memorandum letterhead ready for print / PDF archiving."""
    memo = get_object_or_404(Message.objects.select_related(
        'sender', 'recipient', 'sender__department', 'recipient__department', 'acknowledgement'
    ), pk=pk)

    # Permission check: sender, recipient, admin, or hod
    if request.user not in (memo.sender, memo.recipient) and not request.user.is_superuser and not _is_hod(request.user):
        messages.error(request, 'Permission Denied: You do not have authorization to export this official document.')
        return redirect('inbox')

    minutes = memo.minutes.select_related('officer', 'officer__department').all()
    acknowledgement = getattr(memo, 'acknowledgement', None)

    return render(request, 'messaging/memo_pdf.html', {
        'memo': memo,
        'minutes': minutes,
        'acknowledgement': acknowledgement,
    })


# ---------------------------------------------------------------------------
# Central Records Registry & Archive (Feature 11)
# ---------------------------------------------------------------------------

@login_required
def records_archive_view(request):
    """Central searchable registry of all council memos for leadership, registry & HODs."""
    if not (request.user.is_superuser or request.user.role in ('ADMIN', 'HOD')):
        messages.error(request, 'Access Denied: The central records registry is restricted to Council Administrators and Department Heads.')
        return redirect('inbox')

    memos_qs = Message.objects.filter(status='approved').select_related(
        'sender', 'recipient', 'sender__department', 'recipient__department', 'acknowledgement'
    ).order_by('-timestamp')

    q = request.GET.get('q', '').strip()
    dept_id = request.GET.get('dept', '').strip()
    priority = request.GET.get('priority', '').strip()
    date_from = request.GET.get('from', '').strip()
    date_to = request.GET.get('to', '').strip()

    if q:
        memos_qs = memos_qs.filter(
            Q(ref_number__icontains=q) |
            Q(subject__icontains=q) |
            Q(body__icontains=q) |
            Q(sender__first_name__icontains=q) |
            Q(sender__last_name__icontains=q) |
            Q(recipient__first_name__icontains=q) |
            Q(recipient__last_name__icontains=q)
        )
    if dept_id:
        memos_qs = memos_qs.filter(
            Q(sender__department_id=dept_id) | Q(recipient__department_id=dept_id)
        )
    if priority:
        memos_qs = memos_qs.filter(priority=priority)
    if date_from:
        memos_qs = memos_qs.filter(timestamp__date__gte=date_from)
    if date_to:
        memos_qs = memos_qs.filter(timestamp__date__lte=date_to)

    # Optional CSV Export of Registry Search Results
    if request.GET.get('export') == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="CWS_Registry_Archive_{timezone.now():%Y%m%d}.csv"'
        writer = csv.writer(response)
        writer.writerow(['Reference Number', 'Priority', 'Subject', 'Sender', 'Sender Dept', 'Recipient', 'Recipient Dept', 'Dispatched At', 'Is Read', 'Read At', 'Acknowledged'])
        for m in memos_qs[:500]:
            ack_text = f"Yes ({m.acknowledgement.acknowledged_at:%Y-%m-%d %H:%M})" if hasattr(m, 'acknowledgement') else "No"
            writer.writerow([
                m.ref_number, m.priority, m.subject,
                m.sender.get_full_name(), getattr(m.sender.department, 'name', 'General Line'),
                m.recipient.get_full_name(), getattr(m.recipient.department, 'name', 'General Line'),
                m.timestamp.strftime('%Y-%m-%d %H:%M'),
                'Yes' if m.is_read else 'No',
                m.read_at.strftime('%Y-%m-%d %H:%M') if m.read_at else 'N/A',
                ack_text
            ])
        return response

    departments = User.objects.none()  # placeholder
    from accounts.models import Department
    departments = Department.objects.all().order_by('name')

    total_records = memos_qs.count()
    memos_page = memos_qs[:100]

    return render(request, 'messaging/archive.html', {
        'memos': memos_page,
        'total_records': total_records,
        'departments': departments,
        'search_query': q,
        'selected_dept': dept_id,
        'selected_priority': priority,
        'date_from': date_from,
        'date_to': date_to,
    })


# ---------------------------------------------------------------------------
# Internal Notice Board (Feature 17)
# ---------------------------------------------------------------------------

@login_required
def notice_board_view(request):
    """Council Notice Board for meetings, welfare advisories, and internal announcements."""
    notices = NoticeBoardItem.objects.select_related('author', 'author__department').all()

    category_filter = request.GET.get('category', '').strip()
    if category_filter:
        notices = notices.filter(category=category_filter)

    can_post = request.user.is_superuser or getattr(request.user, 'role', '') in ('ADMIN', 'HOD')

    form = None
    if can_post:
        if request.method == 'POST' and request.POST.get('action') == 'post_notice':
            form = NoticeBoardForm(request.POST, request.FILES)
            if form.is_valid():
                notice = form.save(commit=False)
                notice.author = request.user
                notice.save()
                messages.success(request, f'Notice "{notice.title}" posted to the bulletin board.')
                return redirect('notice_board')
        else:
            form = NoticeBoardForm()

    return render(request, 'messaging/notice_board.html', {
        'notices': notices,
        'form': form,
        'can_post': can_post,
        'selected_category': category_filter,
    })


# ---------------------------------------------------------------------------
# In-App Notifications API & Handlers (Feature 10)
# ---------------------------------------------------------------------------

@login_required
def notifications_list_view(request):
    """Full notifications inbox for the current officer."""
    notifs = request.user.notifications.select_related('actor').all()[:50]
    return render(request, 'messaging/notifications_list.html', {'notifications': notifs})


@login_required
def mark_notification_read_view(request, pk):
    """Mark a notification as read and redirect to target URL."""
    notif = get_object_or_404(Notification, pk=pk, recipient=request.user)
    notif.is_read = True
    notif.save(update_fields=['is_read'])
    if notif.target_url:
        return redirect(notif.target_url)
    return redirect('notifications_list')


@login_required
def mark_all_notifications_read_view(request):
    """Mark all notifications as read for current user."""
    request.user.notifications.filter(is_read=False).update(is_read=True)
    messages.success(request, 'All notifications marked as read.')
    return redirect('notifications_list')
