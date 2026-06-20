from django.conf import settings
from django.db import models

from team_finder.constants import (
    PROJECT_NAME_MAX_LENGTH,
    PROJECT_STATUS_MAX_LENGTH,
    SKILL_NAME_MAX_LENGTH,
)


class Skill(models.Model):
    name = models.CharField("name", max_length=SKILL_NAME_MAX_LENGTH, unique=True)

    class Meta:
        verbose_name = "skill"
        verbose_name_plural = "skills"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Project(models.Model):
    class Status(models.TextChoices):
        OPEN = "open", "Открыт"
        CLOSED = "closed", "Закрыт"

    name = models.CharField("name", max_length=PROJECT_NAME_MAX_LENGTH)
    description = models.TextField("description", blank=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="owned_projects",
        on_delete=models.CASCADE,
        verbose_name="owner",
    )
    created_at = models.DateTimeField("created at", auto_now_add=True)
    github_url = models.URLField("github url", blank=True)
    status = models.CharField(
        "status",
        max_length=PROJECT_STATUS_MAX_LENGTH,
        choices=Status.choices,
        default=Status.OPEN,
    )
    participants = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="participated_projects",
        blank=True,
        verbose_name="participants",
    )
    skills = models.ManyToManyField(
        Skill, related_name="projects", blank=True, verbose_name="skills"
    )

    class Meta:
        verbose_name = "project"
        verbose_name_plural = "projects"
        ordering = ["-created_at"]

    def __str__(self):
        return self.name
