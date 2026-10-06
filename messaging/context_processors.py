from .models import Message

def unread_message_count(request):
    if request.user.is_authenticated:
        # Count unread messages addressed to the logged-in user
        count = Message.objects.filter(recipient=request.user, is_read=False).count()
        return {'unread_count': count}
    return {'unread_count': 0}