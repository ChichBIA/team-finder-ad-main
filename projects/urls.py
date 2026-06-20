from django.urls import path

from . import views

app_name = "projects"

urlpatterns = [
    path("list/", views.project_list, name="list"),
    path("favorites/", views.favorite_projects, name="favorites"),
    path("create-project/", views.project_create, name="create"),
    path("skills/", views.skills_search, name="skills_search"),
    path("<int:project_id>/", views.project_detail, name="detail"),
    path("<int:project_id>/edit/", views.project_edit, name="edit"),
    path("<int:project_id>/complete/", views.complete_project, name="complete"),
    path(
        "<int:project_id>/toggle-favorite/",
        views.toggle_favorite,
        name="toggle_favorite",
    ),
    path(
        "<int:project_id>/toggle-participate/",
        views.toggle_participate,
        name="toggle_participate",
    ),
    path("<int:project_id>/skills/add/", views.skills_add, name="skills_add"),
    path(
        "<int:project_id>/skills/<int:skill_id>/remove/",
        views.skills_remove,
        name="skills_remove",
    ),
]
