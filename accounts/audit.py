from .models import AuditLog

def get_client_ip(request):
    if not request:
        return None
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def log_audit(request, action, description, user=None):
    """Helper to log security and administrative events to the immutable audit trail."""
    try:
        actor = user or (request.user if request and request.user.is_authenticated else None)
        ip = get_client_ip(request)
        return AuditLog.objects.create(
            user=actor,
            action=action,
            description=description,
            ip_address=ip
        )
    except Exception:
        return None
