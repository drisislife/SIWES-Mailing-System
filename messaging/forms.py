from django import forms
from .models import Message
from accounts.models import CustomUser

class ComposeMessageForm(forms.ModelForm):
    # Allow the sender to pick who they are sending the memo to
    recipient = forms.ModelChoiceField(
        queryset=CustomUser.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        empty_label="Select a Staff Member"
    )

    class Meta:
        model = Message
        fields = ['recipient', 'subject', 'body']
        widgets = {
            'subject': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Memo Subject'}),
            'body': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Type your memo here...'}),
        }