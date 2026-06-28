from django import forms
from django.contrib.auth.forms import AuthenticationForm

from .models import User


class RegisterForm(forms.ModelForm):
    password1 = forms.CharField(
        label="Пароль",
        widget=forms.PasswordInput
    )

    password2 = forms.CharField(
        label="Повторите пароль",
        widget=forms.PasswordInput
    )

    class Meta:
        model = User
        fields = (
            "username",
            "email",
        )
        labels = {
            "username": "Логин",
            "email": "Email",
        }

    def clean_username(self):
        username = self.cleaned_data.get("username", "").strip()

        if not username:
            raise forms.ValidationError("Введите логин.")

        if len(username) < 3:
            raise forms.ValidationError("Логин должен содержать минимум 3 символа.")

        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("Пользователь с таким логином уже существует.")

        return username

    def clean_email(self):
        email = self.cleaned_data.get("email", "").strip()

        if not email:
            raise forms.ValidationError("Введите email.")

        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Пользователь с таким email уже существует.")

        return email

    def clean_password1(self):
        password1 = self.cleaned_data.get("password1")

        if password1 and len(password1) < 8:
            raise forms.ValidationError("Пароль должен содержать минимум 8 символов.")

        return password1

    def clean(self):
        cleaned_data = super().clean()

        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")

        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Пароли не совпадают.")

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])

        if commit:
            user.save()

        return user


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        label="Логин",
        error_messages={
            "required": "Введите логин.",
        },
        widget=forms.TextInput(attrs={
            "autofocus": True
        })
    )

    password = forms.CharField(
        label="Пароль",
        error_messages={
            "required": "Введите пароль.",
        },
        widget=forms.PasswordInput
    )

    error_messages = {
        "invalid_login": "Неверный логин или пароль.",
        "inactive": "Этот аккаунт отключён.",
    }