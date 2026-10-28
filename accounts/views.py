from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate, get_user_model
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_protect
from django.contrib import messages
from .forms import (
    CustomUserCreationForm, UserLoginForm, UserProfileForm,
    ProcurementMemoCreationForm, QuotesAndVoucherForm, ProcurementActionForm
)
from .models import Department, ProcurementMemo, ProcurementActionLog

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
            login(request, user)
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
    logout(request)
    messages.success(request, 'You have been successfully logged out.')
    return redirect('login')


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
    from messaging.models import Message
    from accounts.models import ProcurementMemo

    user = request.user

    # Recent received memos
    recent_received = Message.objects.filter(
        recipient=user,
        status='approved'
    ).order_by('-timestamp')[:5]

    # Recent sent memos
    recent_sent = Message.objects.filter(
        sender=user
    ).order_by('-timestamp')[:4]

    # Active procurement vouchers
    active_vouchers = ProcurementMemo.objects.filter(
        originating_department=user.department
    ).exclude(
        current_status__in=['COMPLETED', 'REJECTED']
    ).order_by('-updated_at')[:4] if user.department else []

    total_memos_count = Message.objects.filter(recipient=user).count()
    delivered_memos_count = Message.objects.filter(recipient=user, status='approved').count()

    return render(request, 'accounts/dashboard.html', {
        'recent_received': recent_received,
        'recent_sent': recent_sent,
        'active_vouchers': active_vouchers,
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
        return dept_code == 'PAY_OFFICE' and is_hod

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