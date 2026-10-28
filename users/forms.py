from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import Group

from django.contrib.auth.forms import SetPasswordForm
from django.contrib.auth.models import User

User = get_user_model()

# Role aktif aplikasi (v1.2+): Crew tidak dipakai.
ACTIVE_ROLES = (
    ("Sales Admin", "Sales Admin"),
    ("Dispatch", "Dispatch"),
    ("Manager", "Manager"),
    ("Accounting", "Accounting")
)


def role_choices():
    return [("", "— Tanpa role —")] + list(ACTIVE_ROLES)


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        label="Username",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Masukkan username",
                "autofocus": True,
            }
        ),
    )
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Masukkan password",
            }
        ),
    )


class UserCreateForm(forms.ModelForm):
    role = forms.ChoiceField(
        choices=role_choices,
        required=False,
        label="Role",
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(
                attrs={"class": "form-control", "autocomplete": "new-password"}
        ), 
        required=False
    )

    class Meta:
            model = User
            fields = ["username", "first_name", "last_name",]
            widgets = {
                "username": forms.TextInput(attrs={"class": "form-control"}),
                "first_name": forms.TextInput(attrs={"class": "form-control"}),
                "last_name": forms.TextInput(attrs={"class": "form-control"}),
            }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        is_edit_mode = self.instance and self.instance.pk and not self.instance._state.adding
        if is_edit_mode:
            self.fields['password'].required = False
            self.fields['password'].help_text = "Biarkan kosong jika tidak ingin mengubah password."
            del self.fields['role']
        else:
            self.fields['password'].required = True

    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data.get('password')
        if password:
            user.set_password(password)
        elif not self.instance.pk:
            user.set_password(password)

        if commit:
            user.save()
        return user

    def _save_role(self, user):
        role = self.cleaned_data.get("role")
        user.groups.clear()
        if role:
            group, _ = Group.objects.get_or_create(name=role)
            user.groups.add(group)

    def clean_username(self):
        username = self.cleaned_data.get("username")
        query = User.objects.filter(username=username)
        if self.instance and self.instance.pk:
            query = query.exclude(pk=self.instance.pk)
            
        if query.exists():
            raise forms.ValidationError("Username sudah dipakai.")
        return username

    
    
class UserRoleForm(forms.Form):
    """Ubah role (group) seorang user."""

    role = forms.ChoiceField(
        choices=role_choices,
        required=False,
        label="Role",
        widget=forms.Select(attrs={"class": "form-select form-select-sm"}),
    )


class UserChangePasswordForm(SetPasswordForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Tambahkan class CSS Bootstrap dan placeholder ke semua field
        for field_name, field in self.fields.items():
            field.widget.attrs.update({
                'class': 'form-control',
                'autocomplete': 'new-password'
            })
            
        self.fields['new_password1'].label = "Kata Sandi Baru"
        self.fields['new_password1'].widget.attrs['placeholder'] = "Masukkan kata sandi baru"
        
        self.fields['new_password2'].label = "Konfirmasi Kata Sandi Baru"
        self.fields['new_password2'].widget.attrs['placeholder'] = "Ulangi kata sandi baru"

class UserPasswordForm(forms.Form):
    """Reset password user (khusus superadmin)."""

    new_password = forms.CharField(
        label="Password baru",
        min_length=8,
        widget=forms.PasswordInput(
            attrs={"class": "form-control", "autocomplete": "new-password"}
        ),
    )
    confirm_password = forms.CharField(
        label="Ulangi password",
        widget=forms.PasswordInput(
            attrs={"class": "form-control", "autocomplete": "new-password"}
        ),
    )

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get("new_password")
        p2 = cleaned.get("confirm_password")
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("Konfirmasi password tidak sama.")
        return cleaned
