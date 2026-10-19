from django import forms
from django.contrib.auth import get_user_model
from .models import Message

User = get_user_model()


class MessageForm(forms.ModelForm):
    """Form for composing a new inter-departmental memo."""
    recipient = forms.ModelChoiceField(
        queryset=User.objects.filter(account_approved=True).exclude(role='ADMIN'),
        widget=forms.Select(attrs={'class': 'form-select'}),
        empty_label='Select a Staff Member'
    )

    class Meta:
        model = Message
        fields = ['recipient', 'subject', 'body']
        widgets = {
            'subject': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Memo Subject'
            }),
            'body': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6,
                'placeholder': 'Type your memo here...'
            }),
        }