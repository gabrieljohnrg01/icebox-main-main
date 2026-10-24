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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].required = True

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
            'name': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
                'email': forms.EmailInput(attrs={'class': 'form-control'}),
                'contact_number': forms.TextInput(attrs={'class': 'form-control'}),
            'logo': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super(StartupForm, self).__init__(*args, **kwargs)
        self.fields['email'].required = True
        self.fields['contact_number'].required = True
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

    def clean_logo(self):
        logo = self.cleaned_data.get('logo')
        if logo and hasattr(logo, 'name'):
            from .validators import validate_image_file
            is_valid, err = validate_image_file(logo)
            if not is_valid:
                raise forms.ValidationError(err)
        return logo

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

    first_name = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'First Name'
        })
    )

    middle_name = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Middle Name (Optional)'
        })
    )

    last_name = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Last Name'
        })
    )

    position = forms.ChoiceField(
        choices=[
            ('', 'Select Position'),
            ('CEO', 'Chief Executive Officer'),
            ('CTO', 'Chief Technology Officer'),
            ('CFO', 'Chief Financial Officer'),
            ('COO', 'Chief Operating Officer'),
            ('OTHER', 'Other'),
        ],
        required=True,
        widget=forms.Select(attrs={
            'class': 'form-control',
            'id': 'position-select'
        })
    )

    other_position = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter Position',
            'id': 'other-position'
        })
    )

    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Email Address'
        })
    )

    contact_number = forms.CharField(
        max_length=20,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Contact Number'
        })
    )

    def clean(self):
        cleaned_data = super().clean()

        position = cleaned_data.get('position')
        other_position = cleaned_data.get('other_position')

        if position == 'OTHER':
            if not other_position:
                self.add_error(
                    'other_position',
                    'Please specify the position.'
                )
            else:
                cleaned_data['position'] = other_position

        return cleaned_data