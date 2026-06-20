import re
from urllib.parse import urlparse

from django import forms
from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from .models import User

PHONE_RE = re.compile(r"^(8\d{10}|\+7\d{10})$")


class RegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ("name", "surname", "email", "password")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"].strip().lower()
        user.set_password(self.cleaned_data["password"])
        if not commit:
            return user

        try:
            user.save()
        except IntegrityError as exc:
            raise ValidationError("Пользователь с таким email уже существует") from exc

        return user


class LoginForm(forms.Form):
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request", None)
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get("email")
        password = cleaned_data.get("password")

        if email and password:
            user = authenticate(self.request, email=email, password=password)
            if user is None:
                raise ValidationError("Неверный имейл или пароль")
            cleaned_data["user"] = user

        return cleaned_data


class ProfileEditForm(forms.ModelForm):
    github_url = forms.CharField(required=False)

    class Meta:
        model = User
        fields = ("name", "surname", "avatar", "about", "phone", "github_url")

    def clean_phone(self):
        phone = self.cleaned_data.get("phone")
        if not phone:
            return None
        phone = phone.strip()

        if not PHONE_RE.match(phone):
            raise ValidationError(
                "Телефон должен быть в формате 8XXXXXXXXXX или +7XXXXXXXXXX"
            )

        if phone.startswith("8"):
            phone = "+7" + phone[1:]

        qs = User.objects.filter(phone=phone)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError("Пользователь с таким телефоном уже существует")

        return phone

    def clean_github_url(self):
        value = (self.cleaned_data.get("github_url") or "").strip()
        if not value:
            return value

        if not value.startswith(("http://", "https://")):
            value = f"https://{value}"

        parsed = urlparse(value)
        if not parsed.netloc or not parsed.netloc.lower().endswith("github.com"):
            raise ValidationError("Ссылка должна вести на github.com")

        return value
