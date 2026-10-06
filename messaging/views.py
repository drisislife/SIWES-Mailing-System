from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Message
from .forms import ComposeMessageForm

@login_required
def inbox(request):
    # FIXED: Changed -created_at to -timestamp to match your database
    received_memos = Message.objects.filter(recipient=request.user, status='DELIVERED').order_by('-timestamp')
    
    # Calculate how many are unread
    unread_count = received_memos.filter(is_read=False).count()
    
    return render(request, 'messaging/inbox.html', {
        'memos': received_memos,
        'unread_count': unread_count
    })

@login_required
def compose_memo(request):
    if request.method == 'POST':
        form = ComposeMessageForm(request.POST)
        if form.is_valid():
            memo = form.save(commit=False)
            memo.sender = request.user
            
            # THE HOD INTERCEPT LOGIC
            if getattr(request.user, 'department', None) == getattr(memo.recipient, 'department', None) and request.user.department is not None:
                memo.status = 'DELIVERED'
                messages.success(request, f"Memo sent instantly to {memo.recipient.email}!")
            else:
                memo.status = 'PENDING_HOD'
                messages.warning(request, f"Memo to {memo.recipient.email} requires HOD approval because they are in a different department.")
            
            memo.save()
            return redirect('inbox')
    else:
        form = ComposeMessageForm()
        
    return render(request, 'messaging/compose.html', {'form': form})