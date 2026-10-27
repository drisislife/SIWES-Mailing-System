from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import CustomUser, ProcurementMemo, Department

class CustomUserCreationForm(UserCreationForm):
    first_name = forms.CharField(
        max_length=150,
        required=True,
        label="First Name",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your first name'
        })
    )
    last_name = forms.CharField(
        max_length=150,
        required=True,
        label="Surname / Last Name",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your surname'
        })
    )
    email = forms.EmailField(
        required=True,
        label="Official Email Address",
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'name@council.gov.ng or email'
        })
    )
    department = forms.ModelChoiceField(
        queryset=Department.objects.all(),
        required=False,
        empty_label="Select Council Department (Optional)",
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Department"
    )

    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = ('first_name', 'last_name', 'email', 'department')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'password1' in self.fields:
            self.fields['password1'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Create secure password'})
        if 'password2' in self.fields:
            self.fields['password2'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Confirm password'})

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        if CustomUser.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email address already exists.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data['first_name'].strip()
        user.last_name = self.cleaned_data['last_name'].strip()
        user.email = self.cleaned_data['email']
        user.department = self.cleaned_data.get('department')
        user.username = self.cleaned_data['email']
        if commit:
            user.save()
        return user


class UserProfileForm(forms.ModelForm):
    """Profile editing form for staff to update their names, position, and department."""
    first_name = forms.CharField(
        max_length=150,
        required=True,
        label="First Name",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    last_name = forms.CharField(
        max_length=150,
        required=True,
        label="Surname / Last Name",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    position = forms.CharField(
        max_length=150,
        required=False,
        label="Position / Designation",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g. Senior ICT Officer, Assistant Director'
        })
    )
    department = forms.ModelChoiceField(
        queryset=Department.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Assigned Department"
    )

    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'position', 'department']

from django.contrib.auth import authenticate

class UserLoginForm(forms.Form):
    """Email and Password only login form."""
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'name@cws.local or your email',
            'autofocus': 'autofocus'
        }),
        label="Email Address"
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Enter your password'
        }),
        label="Password"
    )

    def __init__(self, request=None, *args, **kwargs):
        self.request = request
        self.user_cache = None
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        password = cleaned_data.get('password')

        if email and password:
            # Find the user by email address (case-insensitive)
            user_obj = CustomUser.objects.filter(email__iexact=email.strip()).first()
            if not user_obj:
                raise forms.ValidationError("No account found with this email address.")

            # Authenticate with the matched user's username & password
            self.user_cache = authenticate(
                self.request,
                username=user_obj.username,
                password=password
            )
            if self.user_cache is None:
                raise forms.ValidationError("Incorrect password. Please try again.")

        return cleaned_data

    def get_user(self):
        return self.user_cache



class ProcurementMemoCreationForm(forms.ModelForm):
    """Initial memo creation form for any originating line department staff."""
    class Meta:
        model = ProcurementMemo
        fields = ['title', 'description', 'estimated_amount', 'memo_document']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. Procurement of ICT Server Hardware & Accessories'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Provide full details, justification, and specifications for this request...'
            }),
            'estimated_amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0.00'
            }),
            'memo_document': forms.ClearableFileInput(attrs={
                'class': 'form-control'
            }),
        }


class QuotesAndVoucherForm(forms.ModelForm):
    """Used in Step 4 when memo returns to Originating Dept to upload quotes and calculate voucher."""
    class Meta:
        model = ProcurementMemo
        fields = ['voucher_number', 'final_voucher_amount', 'quotations_document', 'voucher_document']
        widgets = {
            'voucher_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. VCH-ICT-2026-0042',
                'required': 'required'
            }),
            'final_voucher_amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0.00',
                'required': 'required'
            }),
            'quotations_document': forms.ClearableFileInput(attrs={
                'class': 'form-control'
            }),
            'voucher_document': forms.ClearableFileInput(attrs={
                'class': 'form-control'
            }),
        }


class ProcurementActionForm(forms.Form):
    """Standard action form for approving, signing off, releasing, or rejecting at any stage."""
    comments = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Add remarks, minute, audit notes, or reasons for rejection...'
        })
    )