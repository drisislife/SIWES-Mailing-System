from django.contrib.auth import get_user_model
from messaging.models import Message, CouncilCircular
from accounts.models import ProcurementMemo

User = get_user_model()


def cws_global_context(request):
    """Provides navigation counts and team members for the inspired sidebar UI."""
    if not request.user.is_authenticated:
        return {}

    user = request.user

    # Unread messages for the current user
    unread_count = Message.objects.filter(
        recipient=user,
        status='approved',
        is_read=False
    ).count()

    # Pending HOD approvals count
    pending_approvals = 0
    if user.is_superuser or getattr(user, 'role', '') == 'ADMIN':
        pending_approvals = Message.objects.filter(status='pending_hod').count()
    elif getattr(user, 'role', '') == 'HOD' and user.department:
        pending_approvals = Message.objects.filter(
            sender__department=user.department,
            status='pending_hod'
        ).count()

    # Active Procurement vouchers count
    active_vouchers = ProcurementMemo.objects.exclude(
        current_status__in=['COMPLETED', 'REJECTED']
    ).count()

    # Active Council Circulars count
    active_circulars_count = CouncilCircular.objects.filter(is_active=True).count()

    # Team members widget (mirroring inspo sidebar)
    # Prefer colleagues in same department, else other staff
    colleagues_qs = User.objects.filter(account_approved=True).exclude(pk=user.pk)
    if user.department:
        dept_colleagues = list(colleagues_qs.filter(department=user.department)[:3])
        if len(dept_colleagues) < 3:
            more_colleagues = list(colleagues_qs.exclude(department=user.department)[:3 - len(dept_colleagues)])
            team_members = dept_colleagues + more_colleagues
        else:
            team_members = dept_colleagues
    else:
        team_members = list(colleagues_qs[:3])

    return {
        'sidebar_unread_count': unread_count,
        'sidebar_pending_approvals_count': pending_approvals,
        'sidebar_active_vouchers_count': active_vouchers,
        'sidebar_circulars_count': active_circulars_count,
        'sidebar_team_members': team_members,
    }
