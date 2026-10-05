from django import forms
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm, UserCreationForm

from .models import User


class StyledFormMixin:
    """Adds the shared CSS classes to every widget."""

    def style_fields(self):
        for field in self.fields.values():
            widget = field.widget
            if isinstance(widget, forms.CheckboxInput):
                widget.attrs.setdefault("class", "check")
            elif isinstance(widget, forms.Select):
                widget.attrs.setdefault("class", "input select")
            else:
                widget.attrs.setdefault("class", "input")


class LoginForm(StyledFormMixin, AuthenticationForm):
    error_messages = {
        **AuthenticationForm.error_messages,
        "invalid_login": "Incorrect email or password. Please try again.",
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].label = "Email"
        self.fields["username"].widget = forms.EmailInput(
            attrs={"autofocus": True, "placeholder": "you@example.com", "autocomplete": "email"}
        )
        self.fields["password"].widget.attrs.update({"placeholder": "Password"})
        self.style_fields()


class BaseSignupForm(StyledFormMixin, UserCreationForm):
    """Collects the person's name, email and password. The email doubles as the internal username."""

    role = User.STUDENT

    class Meta:
        model = User
        fields = ("first_name", "last_name", "email")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["first_name"].label = "First name"
        self.fields["last_name"].label = "Last name"
        self.fields["email"].label = "Email"
        for name in ("first_name", "last_name", "email"):
            self.fields[name].required = True
        self.fields["first_name"].widget.attrs.update({"placeholder": "e.g. Meena", "autocomplete": "given-name"})
        self.fields["last_name"].widget.attrs.update({"placeholder": "e.g. Iyer", "autocomplete": "family-name"})
        self.fields["email"].widget.attrs.update({"placeholder": "you@example.com", "autocomplete": "email"})
        self.fields["password1"].label = "Password"
        self.fields["password2"].label = "Confirm password"
        self.style_fields()

    def clean_first_name(self):
        return " ".join(self.cleaned_data["first_name"].split()).title()

    def clean_last_name(self):
        return " ".join(self.cleaned_data["last_name"].split()).title()

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if len(email) > 150:
            raise forms.ValidationError("Please use an email address under 150 characters.")
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = user.email  # the email doubles as the internal username
        user.role = self.role
        if commit:
            user.save()
        return user


class StudentSignupForm(BaseSignupForm):
    role = User.STUDENT


class TeacherCreateForm(BaseSignupForm):
    role = User.TEACHER


class ProfileForm(StyledFormMixin, forms.ModelForm):
    """Lets a signed-in user edit their own name."""

    class Meta:
        model = User
        fields = ("first_name", "last_name")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["first_name"].label = "First name"
        self.fields["last_name"].label = "Last name"
        for field in self.fields.values():
            field.required = True
        self.style_fields()

    def clean_first_name(self):
        return " ".join(self.cleaned_data["first_name"].split()).title()

    def clean_last_name(self):
        return " ".join(self.cleaned_data["last_name"].split()).title()


class StyledPasswordChangeForm(StyledFormMixin, PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["old_password"].label = "Current password"
        self.fields["new_password1"].label = "New password"
        self.fields["new_password2"].label = "Confirm new password"
        self.style_fields()
