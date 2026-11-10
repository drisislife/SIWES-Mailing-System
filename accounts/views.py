import csv
import io
import random
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.utils import timezone
from django.db.models import Count, Q
from django.contrib.auth import login, logout, authenticate, get_user_model
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_protect
from django.contrib import messages
from .forms import (
    CustomUserCreationForm, UserLoginForm, UserProfileForm,
    ProcurementMemoCreationForm, QuotesAndVoucherForm, ProcurementActionForm,
    BulkStaffImportForm
)
from .models import Department, ProcurementMemo, ProcurementActionLog, AuditLog
from .audit import log_audit

User = get_user_model()



# ── Auth Views ────────────────────────────────────────────────────────────────

@csrf_protect
def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.account_approved = False
            user.save()
            login(request, user)
            log_audit(request, 'LOGIN', f"User {user.email} successfully logged in", user=user)
            messages.info(
                request,
                f'Welcome to CWS, {user.first_name or user.email}! Your registration was successful. Your account is currently pending Administrator verification; you can explore your workspace, but message sending is restricted until an admin verifies your account.'
            )
            return redirect('dashboard')
        else:
            messages.error(request, 'Registration failed. Please correct the errors below.')
    else:
        form = CustomUserCreationForm()

    return render(request, 'accounts/register.html', {'form': form})


@csrf_protect
def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = UserLoginForm(request=request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if getattr(user, 'two_factor_enabled', False):
                otp = f"{random.randint(100000, 999999)}"
                user.two_factor_otp = otp
                user.two_factor_otp_expiry = timezone.now() + timezone.timedelta(minutes=10)
                user.save(update_fields=['two_factor_otp', 'two_factor_otp_expiry'])
                request.session['pre_2fa_user_id'] = user.id
                messages.info(request, f"Security Notice: Your One-Time Password (OTP) is {otp}. (Simulated email transmission).")
                return redirect('two_factor_verify')
            login(request, user)
            log_audit(request, 'LOGIN', f"User {user.email} successfully logged in", user=user)
            if not getattr(user, 'account_approved', False) and not user.is_superuser:
                messages.warning(
                    request,
                    f'Welcome, {user.first_name or user.email}! Notice: Your account is pending Administrator verification. You cannot compose or dispatch messages until an admin approves your profile.'
                )
            else:
                messages.success(request, f'Welcome back, {user.first_name or user.email}!')
            return redirect('dashboard')
    else:
        form = UserLoginForm(request=request)

    return render(request, 'accounts/login.html', {'form': form})



def logout_view(request):
    if request.user.is_authenticated:
        log_audit(request, 'LOGOUT', f"User {request.user.email} logged out", user=request.user)
    logout(request)

    messages.success(request, 'You have been successfully logged out.')
    return redirect('login')


def two_factor_verify_view(request):
    """Verify 2FA OTP code on login (Feature 16)."""
    user_id = request.session.get('pre_2fa_user_id')
    if not user_id:
        return redirect('login')

    target_user = get_object_or_404(User, id=user_id)

    if request.method == 'POST':
        otp_entered = request.POST.get('otp', '').strip()
        if (
            target_user.two_factor_otp
            and target_user.two_factor_otp == otp_entered
            and target_user.two_factor_otp_expiry
            and timezone.now() <= target_user.two_factor_otp_expiry
        ):
            target_user.two_factor_otp = ''
            target_user.two_factor_otp_expiry = None
            target_user.save(update_fields=['two_factor_otp', 'two_factor_otp_expiry'])
            if 'pre_2fa_user_id' in request.session:
                del request.session['pre_2fa_user_id']

            login(request, target_user)
            log_audit(request, 'LOGIN', f"User {target_user.email} authenticated with 2FA OTP", user=target_user)
            messages.success(request, f'2FA Verified! Welcome back, {target_user.first_name or target_user.email}!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid or expired OTP verification code. Please check and try again.')

    return render(request, 'accounts/two_factor_verify.html', {'target_user': target_user})


@login_required
def profile_view(request):
    """Staff profile page to view and update first name, surname, position, and department."""
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile details have been successfully updated!')
            return redirect('profile')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = UserProfileForm(instance=request.user)

    return render(request, 'accounts/profile.html', {
        'form': form,
    })


@login_required
def dashboard_view(request):
    from messaging.models import Message, CouncilCircular
    from accounts.models import ProcurementMemo

    user = request.user

    # Recent received memos
    recent_received = Message.objects.filter(
        recipient=user,
        status='approved'
    ).select_related('sender', 'sender__department').order_by('-timestamp')[:5]

    # Recent sent memos
    recent_sent = Message.objects.filter(
        sender=user
    ).select_related('recipient', 'recipient__department').order_by('-timestamp')[:4]

    # Active procurement vouchers
    active_vouchers = ProcurementMemo.objects.filter(
        originating_department=user.department
    ).exclude(
        current_status__in=['COMPLETED', 'REJECTED']
    ).order_by('-updated_at')[:4] if user.department else []

    # Active Council Broadcasts / Circulars
    active_circulars = CouncilCircular.objects.filter(is_active=True).select_related('published_by', 'published_by__department')[:3]

    total_memos_count = Message.objects.filter(recipient=user).count()
    delivered_memos_count = Message.objects.filter(recipient=user, status='approved').count()

    return render(request, 'accounts/dashboard.html', {
        'recent_received': recent_received,
        'recent_sent': recent_sent,
        'active_vouchers': active_vouchers,
        'active_circulars': active_circulars,
        'total_memos_count': total_memos_count,
        'delivered_memos_count': delivered_memos_count,
    })


# ── Admin Helper ──────────────────────────────────────────────────────────────

def _require_admin(request):
    return request.user.is_superuser or getattr(request.user, 'role', '') == 'ADMIN'


# ── User Management (Pending Approvals) ───────────────────────────────────────

@login_required
def user_management_view(request):
    if not _require_admin(request):
        messages.error(request, 'Access Denied: You do not have permission to view the User Management portal.')
        return redirect('dashboard')

    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        action = request.POST.get('action')
        target_user = get_object_or_404(User, id=user_id)

        if action == 'approve':
            department_id = request.POST.get('department_id')
            if department_id:
                target_user.department = get_object_or_404(Department, id=department_id)
                target_user.account_approved = True
                target_user.save()
                messages.success(request, f'Account for {target_user.email} has been approved.')
            else:
                messages.error(request, 'You must select a department to approve a user.')

        elif action == 'reject':
            # Safety: do not delete admins/superusers via this view
            if target_user.is_superuser or getattr(target_user, 'role', '') == 'ADMIN':
                messages.error(request, 'Cannot reject an Administrator account through this panel.')
            else:
                email = target_user.email
                target_user.delete()
                messages.success(request, f'Account for {email} rejected and removed.')

        return redirect('user_management')

    unapproved_users = User.objects.filter(account_approved=False)
    departments = Department.objects.all()

    return render(request, 'accounts/user_management.html', {
        'unapproved_users': unapproved_users,
        'departments': departments,
    })


# ── Role Management ───────────────────────────────────────────────────────────

@login_required
def role_management_view(request):
    if not _require_admin(request):
        messages.error(request, 'Access Denied: You do not have permission to manage roles.')
        return redirect('dashboard')

    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        new_role = request.POST.get('new_role')
        target_user = get_object_or_404(User, id=user_id)

        # Safety: only superusers can change another superuser's role
        if target_user.is_superuser and not request.user.is_superuser:
            messages.error(request, 'Only a superuser can edit another superuser account.')
            return redirect('role_management')

        target_user.role = new_role
        target_user.save()
        messages.success(request, f"Successfully updated {target_user.email}'s role to {new_role}.")
        return redirect('role_management')

    # Exclude superusers to prevent accidental lockouts
    active_users = User.objects.filter(account_approved=True, is_superuser=False)
    return render(request, 'accounts/role_management.html', {'active_users': active_users})


# ── Procurement & Voucher Pipeline Views ──────────────────────────────────────

def _can_user_act_on_memo(user, memo):
    """
    Determines if the given user has authority to act (approve/advance/reject)
    on the procurement memo based on its current stage and their department/role.
    """
    if user.is_superuser:
        return True

    status = memo.current_status
    user_dept = user.department
    dept_code = getattr(user_dept, 'code', '')
    is_hod = getattr(user, 'role', '') == 'HOD' or getattr(user, 'role', '') == 'ADMIN'

    # Step 1: Originating HOD approves initial memo
    if status == 'PENDING_ORIGINATING_HOD':
        return is_hod and (user_dept == memo.originating_department)

    # Step 2: Council Manager approves initial memo
    if status == 'PENDING_CM_APPROVAL_1':
        return dept_code == 'CM' and is_hod

    # Step 3: Procurement Dept reviews
    if status == 'PENDING_PROCUREMENT':
        return dept_code == 'PROCUREMENT' and is_hod

    # Step 4: Originating Dept attaches quotes and prepares voucher
    if status == 'PENDING_QUOTES_VOUCHER':
        return user_dept == memo.originating_department

    # Step 5: Council Manager approves voucher
    if status == 'PENDING_CM_APPROVAL_2':
        return dept_code == 'CM' and is_hod

    # Step 6: Budget Dept verification
    if status == 'PENDING_BUDGET':
        return dept_code == 'BUDGET' and is_hod

    # Step 7: Internal Audit Office sign-off
    if status == 'PENDING_AUDIT':
        return dept_code == 'AUDIT' and is_hod

    # Step 8: Pay Office / Treasury release
    if status == 'PENDING_PAY_OFFICE':
        return (dept_code in ('PAY_OFFICE', 'BUDGET', 'CM')) and is_hod

    # Step 9: Funds released to Originating HOD - HOD acknowledges & contracts
    if status == 'FUNDS_RELEASED_TO_HOD':
        return is_hod and (user_dept == memo.originating_department)

    return False


@login_required
def procurement_dashboard_view(request):
    """
    Central hub for the procurement pipeline:
    Shows all memos in progress, actionable memos for the user, and recent audit logs.
    """
    user = request.user
    user_dept = user.department
    dept_code = getattr(user_dept, 'code', '')

    all_memos = ProcurementMemo.objects.all().order_by('-created_at')

    # Filter memos originating from user's department
    if user_dept:
        my_dept_memos = all_memos.filter(originating_department=user_dept)
    else:
        my_dept_memos = all_memos.filter(originating_user=user)

    # Calculate pending memos requiring this user's department attention
    actionable_memos = []
    for m in all_memos:
        if _can_user_act_on_memo(user, m):
            actionable_memos.append(m)

    return render(request, 'accounts/procurement_dashboard.html', {
        'all_memos': all_memos,
        'my_dept_memos': my_dept_memos,
        'actionable_memos': actionable_memos,
    })


@login_required
def create_procurement_memo_view(request):
    """Any staff member from any department can initiate a procurement memo."""
    if not getattr(request.user, 'account_approved', False) and not request.user.is_superuser:
        messages.warning(request, "Your account is pending Administrator verification. You cannot initiate procurement memos yet.")
        return redirect('procurement_dashboard')

    if not request.user.department:
        messages.error(request, "You must be assigned to an active department before creating a purchase memo.")
        return redirect('procurement_dashboard')

    if request.method == 'POST':
        form = ProcurementMemoCreationForm(request.POST, request.FILES)
        if form.is_valid():
            memo = form.save(commit=False)
            memo.originating_user = request.user
            memo.originating_department = request.user.department
            memo.current_status = 'PENDING_ORIGINATING_HOD'
            memo.save()

            # Record creation in Action Log
            ProcurementActionLog.objects.create(
                memo=memo,
                actor=request.user,
                actor_department=request.user.department,
                action='MEMO_CREATED',
                stage='PENDING_ORIGINATING_HOD',
                comments=f'Memo initiated by {request.user.email} ({request.user.department.name})'
            )

            messages.success(request, f"Procurement memo '{memo.title}' submitted successfully. Forwarded to your HOD for Step 1 approval.")
            return redirect('procurement_detail', pk=memo.pk)
    else:
        form = ProcurementMemoCreationForm()

    return render(request, 'accounts/procurement_create.html', {'form': form})


@login_required
def procurement_detail_view(request, pk):
    """Detail view showing memo details, current stage, attached documents, and complete timeline."""
    memo = get_object_or_404(ProcurementMemo, pk=pk)
    action_logs = memo.action_logs.all().order_by('timestamp')
    can_act = _can_user_act_on_memo(request.user, memo)

    quotes_voucher_form = QuotesAndVoucherForm(instance=memo) if memo.current_status == 'PENDING_QUOTES_VOUCHER' else None
    action_form = ProcurementActionForm()

    return render(request, 'accounts/procurement_detail.html', {
        'memo': memo,
        'action_logs': action_logs,
        'can_act': can_act,
        'quotes_voucher_form': quotes_voucher_form,
        'action_form': action_form,
    })


@login_required
def advance_procurement_memo_view(request, pk):
    """
    State-machine transitions: advances the memo to the next strict department stage.
    """
    memo = get_object_or_404(ProcurementMemo, pk=pk)

    if not _can_user_act_on_memo(request.user, memo):
        messages.error(request, "Permission denied: You do not have authority to approve or advance this memo at this stage.")
        return redirect('procurement_detail', pk=memo.pk)

    if request.method == 'POST':
        action_type = request.POST.get('action_type', 'APPROVE')
        comments = request.POST.get('comments', '').strip()

        if action_type == 'REJECT':
            memo.current_status = 'REJECTED'
            memo.save()
            ProcurementActionLog.objects.create(
                memo=memo,
                actor=request.user,
                actor_department=request.user.department,
                action='REJECTED',
                stage='REJECTED',
                comments=comments or 'Memo rejected / returned by reviewing officer.'
            )
            messages.warning(request, f"Procurement request '{memo.title}' has been rejected / returned.")
            return redirect('procurement_detail', pk=memo.pk)

        # Transition map for linear progression
        TRANSITIONS = {
            'PENDING_ORIGINATING_HOD': ('PENDING_CM_APPROVAL_1', 'Originating HOD Approved. Forwarded to Council Manager Office.'),
            'PENDING_CM_APPROVAL_1': ('PENDING_PROCUREMENT', 'Council Manager Approved Memo. Forwarded to Procurement Department.'),
            'PENDING_PROCUREMENT': ('PENDING_QUOTES_VOUCHER', 'Procurement Department Approved. Returned to Originating Dept for vendor quotations & voucher calculation.'),
            'PENDING_QUOTES_VOUCHER': ('PENDING_CM_APPROVAL_2', 'Quotations & Voucher generated. Forwarded to Council Manager for voucher sign-off.'),
            'PENDING_CM_APPROVAL_2': ('PENDING_BUDGET', 'Council Manager Approved Voucher. Forwarded to Budget Department for vote book clearance.'),
            'PENDING_BUDGET': ('PENDING_AUDIT', 'Budget Department Verified & Allocated. Forwarded to Internal Audit Office.'),
            'PENDING_AUDIT': ('PENDING_PAY_OFFICE', 'Internal Audit Passed. Forwarded to Pay Office / Treasury for release.'),
            'PENDING_PAY_OFFICE': ('FUNDS_RELEASED_TO_HOD', 'Pay Office / Treasury Released Funds to Originating HOD.'),
            'FUNDS_RELEASED_TO_HOD': ('COMPLETED', 'Originating Department contracted vendor and completed execution.'),
        }

        current_st = memo.current_status

        # Special handling for Step 4: Uploading Quotes & Voucher
        if current_st == 'PENDING_QUOTES_VOUCHER':
            voucher_number = request.POST.get('voucher_number')
            final_voucher_amount = request.POST.get('final_voucher_amount')

            if not voucher_number or not final_voucher_amount:
                messages.error(request, "Voucher Number and Final Voucher Amount are required before advancing.")
                return redirect('procurement_detail', pk=memo.pk)

            memo.voucher_number = voucher_number
            memo.final_voucher_amount = final_voucher_amount

            if 'quotations_document' in request.FILES:
                memo.quotations_document = request.FILES['quotations_document']
            if 'voucher_document' in request.FILES:
                memo.voucher_document = request.FILES['voucher_document']

        next_status, default_msg = TRANSITIONS.get(current_st, (None, None))

        if next_status:
            memo.current_status = next_status
            memo.save()

            ProcurementActionLog.objects.create(
                memo=memo,
                actor=request.user,
                actor_department=request.user.department,
                action=f'ADVANCED_TO_{next_status}',
                stage=next_status,
                comments=comments or default_msg
            )
            messages.success(request, default_msg)
        else:
            messages.info(request, "Memo is already in a terminal state.")

    return redirect('procurement_detail', pk=memo.pk)

# ── Staff Directory (Feature 8) ───────────────────────────────────────────────

@login_required
def staff_directory_view(request):
    """Searchable directory of all council officials and colleagues."""
    staff_qs = User.objects.filter(account_approved=True).select_related('department').order_by('department__name', 'first_name')

    q = request.GET.get('q', '').strip()
    dept_id = request.GET.get('dept', '').strip()
    duty_status = request.GET.get('duty', '').strip()
    role = request.GET.get('role', '').strip()

    if q:
        staff_qs = staff_qs.filter(
            Q(first_name__icontains=q) |
            Q(last_name__icontains=q) |
            Q(email__icontains=q) |
            Q(position__icontains=q)
        )
    if dept_id:
        staff_qs = staff_qs.filter(department_id=dept_id)
    if duty_status:
        staff_qs = staff_qs.filter(duty_status=duty_status)
    if role:
        staff_qs = staff_qs.filter(role=role)

    departments = Department.objects.all().order_by('name')

    return render(request, 'accounts/staff_directory.html', {
        'staff_list': staff_qs,
        'departments': departments,
        'search_query': q,
        'selected_dept': dept_id,
        'selected_duty': duty_status,
        'selected_role': role,
    })


# ── Analytics Dashboard (Feature 6) ───────────────────────────────────────────

@login_required
def analytics_dashboard_view(request):
    """Executive and Administrative analytics for communication volume and accountability."""
    from messaging.models import Message, MessageAcknowledgement

    if not (request.user.is_superuser or request.user.role in ('ADMIN', 'HOD')):
        messages.error(request, 'Access Denied: Analytics is restricted to Heads of Department and Council Executives.')
        return redirect('dashboard')

    total_memos = Message.objects.count()
    delivered_memos = Message.objects.filter(status='approved').count()
    read_memos = Message.objects.filter(is_read=True).count()
    read_rate = round((read_memos / delivered_memos * 100), 1) if delivered_memos else 0
    acknowledged_count = MessageAcknowledgement.objects.count()
    ack_rate = round((acknowledged_count / delivered_memos * 100), 1) if delivered_memos else 0
    recalled_count = Message.objects.filter(status='recalled').count()

    dept_stats = Department.objects.annotate(
        sent_count=Count('employees__sent_messages', distinct=True),
        received_count=Count('employees__received_messages', distinct=True)
    ).order_by('-sent_count')[:10]

    routine_count = Message.objects.filter(priority='ROUTINE').count()
    urgent_count = Message.objects.filter(priority='URGENT').count()
    confidential_count = Message.objects.filter(priority='CONFIDENTIAL').count()

    recent_audits = AuditLog.objects.select_related('user')[:8]

    return render(request, 'accounts/analytics_dashboard.html', {
        'total_memos': total_memos,
        'delivered_memos': delivered_memos,
        'read_memos': read_memos,
        'read_rate': read_rate,
        'acknowledged_count': acknowledged_count,
        'ack_rate': ack_rate,
        'recalled_count': recalled_count,
        'dept_stats': dept_stats,
        'routine_count': routine_count,
        'urgent_count': urgent_count,
        'confidential_count': confidential_count,
        'recent_audits': recent_audits,
    })


# ── Bulk Staff Import (Feature 7) ─────────────────────────────────────────────

@login_required
def bulk_staff_import_view(request):
    """Admin CSV tool to import council personnel rosters."""
    if not _require_admin(request):
        messages.error(request, 'Access Denied: Only Council Administrators can import staff rosters.')
        return redirect('dashboard')

    import_summary = None

    if request.method == 'POST':
        form = BulkStaffImportForm(request.POST, request.FILES)
        if form.is_valid():
            csv_file = request.FILES['csv_file']
            auto_approve = form.cleaned_data['auto_approve']
            default_password = form.cleaned_data['default_password']

            try:
                decoded_file = csv_file.read().decode('utf-8-sig')
                io_string = io.StringIO(decoded_file)
                reader = csv.DictReader(io_string)

                created_count = 0
                updated_count = 0
                errors = []

                for row_idx, row in enumerate(reader, start=2):
                    email = (row.get('email') or '').strip().lower()
                    first_name = (row.get('first_name') or '').strip()
                    last_name = (row.get('last_name') or '').strip()
                    dept_name = (row.get('department') or '').strip()
                    position = (row.get('position') or '').strip()
                    role = (row.get('role') or 'STAFF').strip().upper()

                    if not email:
                        errors.append(f'Row {row_idx}: Missing required email.')
                        continue

                    dept = None
                    if dept_name:
                        dept = Department.objects.filter(
                            Q(name__iexact=dept_name) | Q(name__icontains=dept_name)
                        ).first()

                    valid_roles = ('STAFF', 'HOD', 'ADMIN')
                    user_role = role if role in valid_roles else 'STAFF'

                    user, created = User.objects.get_or_create(
                        username=email,
                        defaults={
                            'email': email,
                            'first_name': first_name,
                            'last_name': last_name,
                            'department': dept,
                            'position': position,
                            'role': user_role,
                            'account_approved': auto_approve,
                        }
                    )

                    if created:
                        user.set_password(default_password)
                        user.save()
                        created_count += 1
                    else:
                        user.first_name = first_name or user.first_name
                        user.last_name = last_name or user.last_name
                        if dept:
                            user.department = dept
                        if position:
                            user.position = position
                        user.role = user_role
                        if auto_approve:
                            user.account_approved = True
                        user.save()
                        updated_count += 1

                log_audit(
                    request,
                    'BULK_IMPORT',
                    f'Imported CSV roster: {created_count} accounts created, {updated_count} updated. Errors: {len(errors)}'
                )

                import_summary = {
                    'created': created_count,
                    'updated': updated_count,
                    'errors': errors,
                }
                messages.success(request, f'Roster processed: {created_count} new accounts added, {updated_count} existing accounts refreshed.')

            except Exception as e:
                messages.error(request, f'Failed to process CSV roster file: {e}')
    else:
        form = BulkStaffImportForm()

    return render(request, 'accounts/bulk_import.html', {
        'form': form,
        'import_summary': import_summary,
    })


def download_sample_roster_csv(request):
    """Download standard sample CSV template for bulk onboarding."""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="CWS_Staff_Roster_Template.csv"'

    writer = csv.writer(response)
    writer.writerow(['first_name', 'last_name', 'email', 'department', 'position', 'role'])
    writer.writerow(['Oladipo', 'Adeyemi', 'o.adeyemi@council.gov.ng', 'ICT', 'Senior Network Engineer', 'STAFF'])
    writer.writerow(['Fatima', 'Bello', 'f.bello@council.gov.ng', 'HR/Admin', 'Head of Personnel', 'HOD'])
    writer.writerow(['Chinedu', 'Okafor', 'c.okafor@council.gov.ng', 'Works', 'Civil Engineer II', 'STAFF'])
    writer.writerow(['Amina', 'Suleiman', 'a.suleiman@council.gov.ng', 'Office of the Council Manager', 'Executive Assistant', 'ADMIN'])

    return response


# ── Audit Log Viewer (Feature 14) ─────────────────────────────────────────────

@login_required
def audit_log_view(request):
    """Central Security and Administrative Audit Trail for Council Leadership."""
    if not _require_admin(request):
        messages.error(request, 'Access Denied: The security audit trail is restricted to Council Administrators.')
        return redirect('dashboard')

    logs = AuditLog.objects.select_related('user', 'user__department').order_by('-created_at')

    action_filter = request.GET.get('action', '').strip()
    search_q = request.GET.get('q', '').strip()

    if action_filter:
        logs = logs.filter(action=action_filter)
    if search_q:
        logs = logs.filter(
            Q(description__icontains=search_q) |
            Q(user__email__icontains=search_q) |
            Q(user__first_name__icontains=search_q) |
            Q(user__last_name__icontains=search_q) |
            Q(ip_address__icontains=search_q)
        )

    logs = logs[:150]
    action_choices = AuditLog.ACTION_CHOICES

    return render(request, 'accounts/audit_log.html', {
        'logs': logs,
        'action_choices': action_choices,
        'selected_action': action_filter,
        'search_query': search_q,
    })
