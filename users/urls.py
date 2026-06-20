from django.urls import path

from . import views

app_name = "users"

urlpatterns = [
    path("register/", views.register, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("list/", views.participants_list, name="list"),
    path("edit-profile/", views.edit_profile, name="edit_profile"),
    path("change-password/", views.change_password, name="change_password"),
    path("skills/", views.skills_search, name="skills_search"),
    path("<int:user_id>/skills/add/", views.skills_add, name="skills_add"),
    path(
        "<int:user_id>/skills/<int:skill_id>/remove/",
        views.skills_remove,
        name="skills_remove",
    ),
    path("<int:user_id>/", views.user_detail, name="detail"),
]
