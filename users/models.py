import random

from django.db import models

from team_finder.constants import (
    USER_ABOUT_MAX_LENGTH,
    USER_NAME_MAX_LENGTH,
    USER_PHONE_MAX_LENGTH,
)

from .managers import UserManager
from .utils import generate_avatar_image
from .constants import (
    AVATAR_SIZE,
    AVATAR_FONT_RATIO,
    AVATAR_TEXT_COLOR,
    AVATAR_COLORS,
    HEX_CHUNK_SIZE,
    HEX_CHUNK_STARTS,
)


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
        bg_color = random.choice(AVATAR_COLORS)
        letter = (self.name or self.email or "?")[0].upper()
        return generate_avatar_image(letter, bg_color)