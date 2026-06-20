import json
import tempfile

from django.test import TestCase, override_settings
from django.urls import reverse

from projects.models import Project
from users.models import User


@override_settings(MEDIA_ROOT=tempfile.gettempdir())
class ProjectViewsTests(TestCase):
    URL_CREATE = "projects:create"
    URL_DETAIL = "projects:detail"
    URL_TOGGLE_FAVORITE = "projects:toggle_favorite"
    URL_TOGGLE_PARTICIPATE = "projects:toggle_participate"
    URL_LIST = "projects:list"
    URL_EDIT = "projects:edit"
    STATUS_OPEN = Project.Status.OPEN
    TEST_EMAIL_OWNER = "owner@example.com"
    TEST_PASSWORD_OWNER = "owner-pass"
    TEST_NAME_OWNER = "Owner"
    TEST_SURNAME_OWNER = "User"
    TEST_EMAIL_MEMBER = "member@example.com"
    TEST_PASSWORD_MEMBER = "member-pass"
    TEST_NAME_MEMBER = "Member"
    TEST_SURNAME_MEMBER = "User"
    TEST_EMAIL_STAFF = "staff@example.com"
    TEST_PASSWORD_STAFF = "staff-pass"
    TEST_NAME_STAFF = "Staff"
    TEST_SURNAME_STAFF = "User"
    PROJECT_NAME_DEMO = "Demo"
    PROJECT_DESCRIPTION_DEMO = "desc"
    PROJECT_NAME_FAVORITE = "Favorite"
    PROJECT_NAME_FAVORITE_GUEST = "Favorite Guest"
    PROJECT_NAME_PARTICIPATE = "Participate"
    PROJECT_NAME_EDIT_TARGET = "Edit Target"
    PROJECT_NAME_UPDATED = "Updated"
    PROJECT_NAME_PREFIX = "Project"
    PROJECT_DESCRIPTION_EMPTY = ""
    HTTP_200_OK = 200
    HTTP_401_UNAUTHORIZED = 401
    JSON_EMPTY = json.dumps({})
    CONTENT_TYPE_JSON = "application/json"

    def setUp(self):
        self.owner = User.objects.create_user(
            email=self.TEST_EMAIL_OWNER,
            password=self.TEST_PASSWORD_OWNER,
            name=self.TEST_NAME_OWNER,
            surname=self.TEST_SURNAME_OWNER,
        )
        self.member = User.objects.create_user(
            email=self.TEST_EMAIL_MEMBER,
            password=self.TEST_PASSWORD_MEMBER,
            name=self.TEST_NAME_MEMBER,
            surname=self.TEST_SURNAME_MEMBER,
        )
        self.staff = User.objects.create_user(
            email=self.TEST_EMAIL_STAFF,
            password=self.TEST_PASSWORD_STAFF,
            name=self.TEST_NAME_STAFF,
            surname=self.TEST_SURNAME_STAFF,
            is_staff=True,
        )

    def test_create_project_adds_owner_as_participant(self):
        self.client.force_login(self.owner)
        response = self.client.post(
            reverse(self.URL_CREATE),
            data={
                "name": self.PROJECT_NAME_DEMO,
                "description": self.PROJECT_DESCRIPTION_DEMO,
                "github_url": "",
                "status": self.STATUS_OPEN,
            },
        )

        project = Project.objects.get(name=self.PROJECT_NAME_DEMO)
        self.assertRedirects(response, reverse(self.URL_DETAIL, args=[project.id]))
        self.assertTrue(project.participants.filter(pk=self.owner.id).exists())

    def test_toggle_favorite(self):
        project = Project.objects.create(
            name=self.PROJECT_NAME_FAVORITE,
            description=self.PROJECT_DESCRIPTION_EMPTY,
            owner=self.owner,
            status=self.STATUS_OPEN,
        )
        self.client.force_login(self.member)

        response = self.client.post(
            reverse(self.URL_TOGGLE_FAVORITE, args=[project.id]),
            data=self.JSON_EMPTY,
            content_type=self.CONTENT_TYPE_JSON,
        )

        self.assertEqual(response.status_code, self.HTTP_200_OK)
        self.assertTrue(self.member.favorites.filter(pk=project.id).exists())

    def test_toggle_favorite_requires_login(self):
        project = Project.objects.create(
            name=self.PROJECT_NAME_FAVORITE_GUEST,
            description=self.PROJECT_DESCRIPTION_EMPTY,
            owner=self.owner,
            status=self.STATUS_OPEN,
        )

        response = self.client.post(
            reverse(self.URL_TOGGLE_FAVORITE, args=[project.id]),
            data=self.JSON_EMPTY,
            content_type=self.CONTENT_TYPE_JSON,
        )

        self.assertEqual(response.status_code, self.HTTP_401_UNAUTHORIZED)

    def test_toggle_participate(self):
        project = Project.objects.create(
            name=self.PROJECT_NAME_PARTICIPATE,
            description=self.PROJECT_DESCRIPTION_EMPTY,
            owner=self.owner,
            status=self.STATUS_OPEN,
        )
        self.client.force_login(self.member)

        response = self.client.post(
            reverse(self.URL_TOGGLE_PARTICIPATE, args=[project.id]),
            data=self.JSON_EMPTY,
            content_type=self.CONTENT_TYPE_JSON,
        )

        self.assertEqual(response.status_code, self.HTTP_200_OK)
        self.assertTrue(project.participants.filter(pk=self.member.id).exists())

    def test_project_list_pagination(self):
        for index in range(13):
            Project.objects.create(
                name=f"{self.PROJECT_NAME_PREFIX} {index}",
                description=self.PROJECT_DESCRIPTION_EMPTY,
                owner=self.owner,
                status=self.STATUS_OPEN,
            )

        response = self.client.get(reverse(self.URL_LIST))
        self.assertEqual(response.status_code, self.HTTP_200_OK)
        self.assertEqual(len(response.context["page_obj"]), 12)

    def test_staff_can_edit_project(self):
        project = Project.objects.create(
            name=self.PROJECT_NAME_EDIT_TARGET,
            description=self.PROJECT_DESCRIPTION_EMPTY,
            owner=self.owner,
            status=self.STATUS_OPEN,
        )
        self.client.force_login(self.staff)

        response = self.client.post(
            reverse(self.URL_EDIT, args=[project.id]),
            data={
                "name": self.PROJECT_NAME_UPDATED,
                "description": self.PROJECT_NAME_UPDATED,  # совпадает с именем в оригинале
                "github_url": "",
                "status": self.STATUS_OPEN,
            },
        )

        self.assertRedirects(response, reverse(self.URL_DETAIL, args=[project.id]))
        project.refresh_from_db()
        self.assertEqual(project.name, self.PROJECT_NAME_UPDATED)
