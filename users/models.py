import random
from io import BytesIO
from pathlib import Path
from uuid import uuid4

from django.conf import settings
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.core.files.base import ContentFile
from django.db import models
from PIL import Image, ImageDraw, ImageFont

from team_finder.constants import (
    USER_ABOUT_MAX_LENGTH,
    USER_NAME_MAX_LENGTH,
    USER_PHONE_MAX_LENGTH,
)


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True")

        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField("email", unique=True)
    name = models.CharField("name", max_length=USER_NAME_MAX_LENGTH)
    surname = models.CharField("surname", max_length=USER_NAME_MAX_LENGTH)
    avatar = models.ImageField("avatar", upload_to="avatars/", blank=True)
    phone = models.CharField(
        "phone", max_length=USER_PHONE_MAX_LENGTH, blank=True, null=True, unique=True
    )
    github_url = models.URLField("github url", blank=True)
    about = models.TextField("about", max_length=USER_ABOUT_MAX_LENGTH, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    favorites = models.ManyToManyField(
        "projects.Project",
        related_name="interested_users",
        blank=True,
    )
    skills = models.ManyToManyField(
        "projects.Skill",
        related_name="users",
        blank=True,
    )

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["name", "surname"]

    class Meta:
        verbose_name = "user"
        verbose_name_plural = "users"
        ordering = ["-id"]

    def __str__(self):
        return f"{self.name} {self.surname}"

    def save(self, *args, **kwargs):
        if not self.avatar:
            self.avatar = self._generate_avatar()
        super().save(*args, **kwargs)

    def _generate_avatar(self):
        size = 256
        bg_color = random.choice(
            [
                "#6C8CBF",
                "#7BAE7F",
                "#B08EA2",
                "#C4A77D",
                "#7A9E9F",
                "#9C7C7C",
            ]
        )
        letter = (self.name or self.email or "?")[0].upper()

        image = Image.new("RGB", (size, size), color=_hex_to_rgb(bg_color))
        draw = ImageDraw.Draw(image)
        font = _load_avatar_font(size)

        text_bbox = draw.textbbox((0, 0), letter, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        position = ((size - text_width) / 2, (size - text_height) / 2)

        draw.text(position, letter, fill=(255, 255, 255), font=font)

        buffer = BytesIO()
        image.save(buffer, format="PNG")
        buffer.seek(0)
        filename = f"avatar_{uuid4().hex}.png"
        return ContentFile(buffer.getvalue(), name=filename)


def _hex_to_rgb(value):
    value = value.lstrip("#")
    return tuple(int(value[i : i + 2], 16) for i in (0, 2, 4))


def _load_avatar_font(size):
    font_path = (
        Path(settings.BASE_DIR)
        / "static"
        / "fonts"
        / "Neue_Haas_Grotesk_Display_Pro_75_Bold.otf"
    )
    font_size = int(size * 0.5)
    if font_path.exists():
        try:
            return ImageFont.truetype(str(font_path), font_size)
        except OSError:
            pass
    return ImageFont.load_default()
