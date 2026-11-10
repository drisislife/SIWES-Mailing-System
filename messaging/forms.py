from django import forms
from django.contrib.auth import get_user_model
from .models import Message, MessageMinute, CouncilCircular, MessageAcknowledgement, NoticeBoardItem, MemoTemplate

User = get_user_model()


class MessageForm(forms.ModelForm):
    """Form for composing a new inter-departmental memo."""
    recipient = forms.ModelChoiceField(
        queryset=User.objects.filter(account_approved=True),
        widget=forms.Select(attrs={'class': 'form-select'}),
        empty_label='Select a Council Official / Colleague'
    )

    class Meta:
        model = Message
        fields = ['recipient', 'priority', 'subject', 'body', 'attachment']
        widgets = {
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'subject': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Official Memorandum Subject'
            }),
            'body': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6,
                'placeholder': 'Type your official memorandum text here...'
            }),
            'attachment': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }


class MessageMinuteForm(forms.ModelForm):
    """Form for adding minutes / notations / endorsements to a memo."""
    class Meta:
        model = MessageMinute
        fields = ['comment']
        widgets = {
            'comment': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter your official minute or directive (e.g. "Approved as recommended", "Referred to Works Dept for inspection")...'
            })
        }


class MessageAcknowledgementForm(forms.ModelForm):
    """Form for recipient to acknowledge receipt of an official memorandum."""
    class Meta:
        model = MessageAcknowledgement
        fields = ['note']
        widgets = {
            'note': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Optional brief acknowledgement remark (e.g., "Noted, action in progress", "Received and forwarded to desk")...'
            })
        }


class CouncilCircularForm(forms.ModelForm):
    """Form for Council Administration to broadcast circulars."""
    class Meta:
        model = CouncilCircular
        fields = ['title', 'priority', 'content', 'attachment']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. Mandatory Departmental Heads Briefing'
            }),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Full content of the circular directive...'
            }),
            'attachment': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }


class NoticeBoardForm(forms.ModelForm):
    """Form to publish notices to the council notice board (Feature 17)."""
    class Meta:
        model = NoticeBoardItem
        fields = ['title', 'category', 'content', 'attachment', 'is_pinned']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Notice Heading / Announcement Subject'
            }),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Enter announcement details, date, time, venue, or notice body...'
            }),
            'attachment': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'is_pinned': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class MemoRecallForm(forms.Form):
    """Form to record reason when recalling/withdrawing a memo (Feature 5)."""
    recall_reason = forms.CharField(
        max_length=255,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Reason for recalling memo (e.g., Attached draft document, figures being updated)...'
        }),
        label="Reason for Recall"
    )
