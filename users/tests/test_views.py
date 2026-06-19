import json
import tempfile

from django.test import TestCase, override_settings
from django.urls import reverse

from projects.models import Project
from users.models import User


@override_settings(MEDIA_ROOT=tempfile.gettempdir())
class UserViewsTests(TestCase):
    def test_register_redirects_to_project_list_and_logs_in(self):
        response = self.client.post(
            reverse("users:register"),
            data={
                "name": "Иван",
                "surname": "Петров",
                "email": "ivan@example.com",
                "password": "testpass123",
            },
        )

        self.assertRedirects(response, reverse("projects:list"))
        user = User.objects.get(email="ivan@example.com")
        self.assertTrue(user.check_password("testpass123"))

        response = self.client.get(reverse("projects:list"))
        self.assertTrue(response.wsgi_request.user.is_authenticated)

    def test_login_shows_error_for_invalid_credentials(self):
        User.objects.create_user(
            email="user@example.com",
            password="correct-pass",
            name="Test",
            surname="User",
        )

        response = self.client.post(
            reverse("users:login"),
            data={"email": "user@example.com", "password": "wrong"},
        )

        self.assertContains(response, "Неверный имейл или пароль")

    def test_participants_filter_participants_of_my_projects(self):
        owner = User.objects.create_user(
            email="owner@example.com",
            password="owner-pass",
            name="Owner",
            surname="User",
        )
        member = User.objects.create_user(
            email="member@example.com",
            password="member-pass",
            name="Member",
            surname="User",
        )
        project = Project.objects.create(
            name="Team Project",
            description="",
            owner=owner,
            status=Project.Status.OPEN,
        )
        project.participants.add(member)

        self.client.force_login(owner)
        response = self.client.get(
            reverse("users:list") + "?filter=participants-of-my-projects"
        )

        self.assertEqual(response.status_code, 200)
        participants = response.context["participants"]
        self.assertIn(member, list(participants))

    def test_edit_profile_accepts_github_without_scheme(self):
        user = User.objects.create_user(
            email="owner@example.com",
            password="owner-pass",
            name="Owner",
            surname="User",
        )
        self.client.force_login(user)

        response = self.client.post(
            reverse("users:edit_profile"),
            data={
                "name": "Owner",
                "surname": "User",
                "about": "",
                "phone": "",
                "github_url": "github.com/user123",
            },
        )

        self.assertRedirects(response, reverse("users:detail", args=[user.id]))
        user.refresh_from_db()
        self.assertEqual(user.github_url, "https://github.com/user123")

    def test_user_skills_add_and_remove(self):
        user = User.objects.create_user(
            email="skills@example.com",
            password="skills-pass",
            name="Skills",
            surname="Owner",
        )
        self.client.force_login(user)

        response = self.client.post(
            reverse("users:skills_add", args=[user.id]),
            data=json.dumps({"name": "Python"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        skill_id = response.json()["id"]
        self.assertTrue(user.skills.filter(pk=skill_id).exists())

        response = self.client.post(
            reverse("users:skills_remove", args=[user.id, skill_id]),
            data=json.dumps({}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        user.refresh_from_db()
        self.assertFalse(user.skills.filter(pk=skill_id).exists())

    def test_user_skills_forbidden_for_other_user(self):
        owner = User.objects.create_user(
            email="owner@example.com",
            password="owner-pass",
            name="Owner",
            surname="User",
        )
        other = User.objects.create_user(
            email="other@example.com",
            password="other-pass",
            name="Other",
            surname="User",
        )
        self.client.force_login(other)

        response = self.client.post(
            reverse("users:skills_add", args=[owner.id]),
            data=json.dumps({"name": "Go"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 403)
