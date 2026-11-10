from .models import Notification

def send_notification(recipient, verb, target_url='', actor=None):
    """Create an in-app notification for an addressed council officer."""
    if not recipient:
        return None
    try:
        return Notification.objects.create(
            recipient=recipient,
            actor=actor,
            verb=verb,
            target_url=target_url
        )
    except Exception:
        return None
