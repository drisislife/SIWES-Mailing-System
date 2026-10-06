from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import CustomUserCreationForm, UserLoginForm
from .models import Department

User = get_user_model()


# ── Auth Views ────────────────────────────────────────────────────────────────

def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.account_approved = False
            user.save()
            messages.success(
                request,
                f'Registration successful for {user.email}! Please wait for an Admin to approve your account.'
            )
            return redirect('login')
        else:
            messages.error(request, 'Registration failed. Please correct the errors below.')
    else:
        form = CustomUserCreationForm()

    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = UserLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if not getattr(user, 'account_approved', True) and not user.is_superuser:
                messages.warning(request, 'Your account is pending Admin approval. You cannot log in yet.')
                return redirect('login')
            login(request, user)
            messages.success(request, f'Welcome back, {user.email}!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid email or password.')
    else:
        form = UserLoginForm()

    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.success(request, 'You have been successfully logged out.')
    return redirect('login')


@login_required
def dashboard_view(request):
    return render(request, 'accounts/dashboard.html')


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