from django import forms
from django.contrib.auth import authenticate
from .models import User, Startup, ProgressReport, StartupMember

class LoginForm(forms.Form):
    username = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control', 
        'placeholder': 'Username',
        'autocomplete': 'username',
        'id': 'id_username'
    }))
    password = forms.CharField(required=False, widget=forms.PasswordInput(attrs={
        'class': 'form-control', 
        'placeholder': 'Password',
        'autocomplete': 'current-password',
        'id': 'id_password'
    }))

class AdminCreationForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_unusable_password()
        user.role = 'admin'
        if commit:
            user.save()
        return user

class StartupForm(forms.ModelForm):
    starting_milestone = forms.ChoiceField(
        choices=[(1, 'Milestone 1'), (2, 'Milestone 2'), (3, 'Milestone 3'), (4, 'Milestone 4')],
        initial=1,
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text="Select which milestone the startup will begin at. Prior milestones will be marked as completed."
    )

    class Meta:
        model = Startup
        fields = ['name', 'description', 'email', 'contact_number', 'logo', 'starting_milestone']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'contact_number': forms.TextInput(attrs={'class': 'form-control'}),
            'logo': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super(StartupForm, self).__init__(*args, **kwargs)
        if self.user and self.instance and self.instance.pk:
            if getattr(self.user, 'role', '') == 'incubatee':
                # Incubatees can ONLY edit logo and description
                for field_name in list(self.fields.keys()):
                    if field_name not in ['logo', 'description']:
                        del self.fields[field_name]
            else:
                # Only owner can edit logo, admins cannot (per user request)
                if self.instance.owner != self.user:
                    if 'logo' in self.fields:
                        del self.fields['logo']

class ProgressReportForm(forms.ModelForm):
    class Meta:
        model = ProgressReport
        fields = ['title', 'description', 'achievements', 'challenges', 'next_steps']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'achievements': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'challenges': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'next_steps': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class StartupMemberForm(forms.Form):
    first_name = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'}))
    middle_name = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Middle Name (Optional)'}))
    last_name = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'}))
    position = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Position (e.g. CEO)'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email Address'}))
    contact_number = forms.CharField(max_length=20, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Contact Number', 'type': 'number', 'pattern': '[0-9]+', 'maxlength': '11'}))
