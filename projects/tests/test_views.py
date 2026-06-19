import json
import tempfile

from django.test import TestCase, override_settings
from django.urls import reverse

from projects.models import Project
from users.models import User


@override_settings(MEDIA_ROOT=tempfile.gettempdir())
class ProjectViewsTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            email="owner@example.com",
            password="owner-pass",
            name="Owner",
            surname="User",
        )
        self.member = User.objects.create_user(
            email="member@example.com",
            password="member-pass",
            name="Member",
            surname="User",
        )
        self.staff = User.objects.create_user(
            email="staff@example.com",
            password="staff-pass",
            name="Staff",
            surname="User",
            is_staff=True,
        )

    def test_create_project_adds_owner_as_participant(self):
        self.client.force_login(self.owner)
        response = self.client.post(
            reverse("projects:create"),
            data={
                "name": "Demo",
                "description": "desc",
                "github_url": "",
                "status": Project.Status.OPEN,
            },
        )

        project = Project.objects.get(name="Demo")
        self.assertRedirects(response, reverse("projects:detail", args=[project.id]))
        self.assertTrue(project.participants.filter(pk=self.owner.id).exists())

    def test_toggle_favorite(self):
        project = Project.objects.create(
            name="Favorite",
            description="",
            owner=self.owner,
            status=Project.Status.OPEN,
        )
        self.client.force_login(self.member)

        response = self.client.post(
            reverse("projects:toggle_favorite", args=[project.id]),
            data=json.dumps({}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(self.member.favorites.filter(pk=project.id).exists())

    def test_toggle_favorite_requires_login(self):
        project = Project.objects.create(
            name="Favorite Guest",
            description="",
            owner=self.owner,
            status=Project.Status.OPEN,
        )

        response = self.client.post(
            reverse("projects:toggle_favorite", args=[project.id]),
            data=json.dumps({}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 401)

    def test_toggle_participate(self):
        project = Project.objects.create(
            name="Participate",
            description="",
            owner=self.owner,
            status=Project.Status.OPEN,
        )
        self.client.force_login(self.member)

        response = self.client.post(
            reverse("projects:toggle_participate", args=[project.id]),
            data=json.dumps({}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(project.participants.filter(pk=self.member.id).exists())

    def test_project_list_pagination(self):
        for index in range(13):
            Project.objects.create(
                name=f"Project {index}",
                description="",
                owner=self.owner,
                status=Project.Status.OPEN,
            )

        response = self.client.get(reverse("projects:list"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["page_obj"]), 12)

    def test_staff_can_edit_project(self):
        project = Project.objects.create(
            name="Edit Target",
            description="",
            owner=self.owner,
            status=Project.Status.OPEN,
        )
        self.client.force_login(self.staff)

        response = self.client.post(
            reverse("projects:edit", args=[project.id]),
            data={
                "name": "Updated",
                "description": "Updated",
                "github_url": "",
                "status": Project.Status.OPEN,
            },
        )

        self.assertRedirects(response, reverse("projects:detail", args=[project.id]))
        project.refresh_from_db()
        self.assertEqual(project.name, "Updated")
