import json
from http import HTTPStatus

from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from projects.models import Skill
from team_finder.constants import SKILLS_SEARCH_LIMIT
from team_finder.pagination import (
    DEFAULT_PAGE_NUMBER,
    DEFAULT_PAGE_SIZE,
    build_query_prefix,
    paginate_queryset,
)

from .forms import LoginForm, ProfileEditForm, RegistrationForm
from .models import User
from .constants import (
    FILTER_OWNERS_OF_FAVORITE_PROJECTS,
    FILTER_OWNERS_OF_PARTICIPATING_PROJECTS,
    FILTER_INTERESTED_IN_MY_PROJECTS,
    FILTER_PARTICIPANTS_OF_MY_PROJECTS,
)


def register(request):
    if request.method == "POST":
        form = RegistrationForm(request.POST or None)
        if not form.is_valid():
            return render(request, "users/register.html", {"form": form})

        user = form.save()
        login(request, user)
        return redirect("projects:list")

    form = RegistrationForm()
    return render(request, "users/register.html", {"form": form})


def login_view(request):
    if request.method == "POST":
        form = LoginForm(request.POST or None, request=request)
        if form.is_valid():
            login(request, form.cleaned_data["user"])
            return redirect("projects:list")
    else:
        form = LoginForm(request=request)

    return render(request, "users/login.html", {"form": form})


def logout_view(request):
    logout(request)
    return redirect("projects:list")


def user_detail(request, user_id):
    profile_user = get_object_or_404(
        User.objects.prefetch_related("owned_projects__participants", "skills"),
        pk=user_id,
    )
    return render(request, "users/user-details.html", {"user": profile_user})


@login_required
def edit_profile(request):
    if request.method == "POST":
        form = ProfileEditForm(
            request.POST or None, request.FILES, instance=request.user
        )
        if not form.is_valid():
            return render(
                request,
                "users/edit_profile.html",
                {"form": form, "user": request.user},
            )

        form.save()
        return redirect("users:detail", user_id=request.user.id)

    form = ProfileEditForm(instance=request.user)
    return render(
        request,
        "users/edit_profile.html",
        {"form": form, "user": request.user},
    )


@login_required
def change_password(request):
    if request.method == "POST":
        form = PasswordChangeForm(user=request.user, data=request.POST or None)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            return redirect("users:detail", user_id=request.user.id)
    else:
        form = PasswordChangeForm(user=request.user)

    return render(request, "users/change_password.html", {"form": form})


def participants_list(request):
    # Оптимизация: подгружаем связанные объекты для избежания N+1
    participants = User.objects.prefetch_related(
        "owned_projects",
        "participated_projects",
        "favorites",
        "skills",
    )
    active_filter = None

    filter_value = request.GET.get("filter")
    if request.user.is_authenticated and filter_value:
        active_filter = filter_value
        if filter_value == FILTER_OWNERS_OF_FAVORITE_PROJECTS:
            participants = User.objects.filter(
                owned_projects__in=request.user.favorites.all()
            ).distinct()
        elif filter_value == FILTER_OWNERS_OF_PARTICIPATING_PROJECTS:
            participants = User.objects.filter(
                owned_projects__in=request.user.participated_projects.all()
            ).distinct()
        elif filter_value == FILTER_INTERESTED_IN_MY_PROJECTS:
            participants = User.objects.filter(
                favorites__owner=request.user
            ).distinct()
        elif filter_value == FILTER_PARTICIPANTS_OF_MY_PROJECTS:
            participants = (
                User.objects.filter(participated_projects__owner=request.user)
                .exclude(pk=request.user.pk)
                .distinct()
            )

    page_obj = paginate_queryset(
        participants,
        request.GET.get("page", DEFAULT_PAGE_NUMBER),
        DEFAULT_PAGE_SIZE,
    )

    return render(
        request,
        "users/participants.html",
        {
            "participants": page_obj.object_list,
            "page_obj": page_obj,
            "active_filter": active_filter,
            "query_prefix": build_query_prefix(filter=active_filter),
        },
    )


def skills_search(request):
    query = request.GET.get("q", "").strip()
    if not query:
        return JsonResponse([], safe=False)

    skills = Skill.objects.filter(name__icontains=query)[:SKILLS_SEARCH_LIMIT]
    return JsonResponse(
        [{"id": skill.id, "name": skill.name} for skill in skills],
        safe=False,
    )


@require_POST
@login_required
def skills_add(request, user_id):
    try:
        target_user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return JsonResponse(
            {"status": "error", "detail": "user_not_found"},
            status=HTTPStatus.NOT_FOUND,
        )

    if request.user != target_user and not request.user.is_staff:
        return JsonResponse(
            {"status": "error", "detail": "forbidden"},
            status=HTTPStatus.FORBIDDEN,
        )

    try:
        payload = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        payload = {}

    skill = None
    skill_id = payload.get("skill_id")
    if skill_id:
        try:
            skill = Skill.objects.get(pk=skill_id)
        except Skill.DoesNotExist:
            return JsonResponse(
                {"status": "error", "detail": "skill_not_found"},
                status=HTTPStatus.NOT_FOUND,
            )
    else:
        name = (payload.get("name") or "").strip()
        if not name:
            return JsonResponse(
                {"status": "error", "detail": "name_required"},
                status=HTTPStatus.BAD_REQUEST,
            )
        skill, _ = Skill.objects.get_or_create(
            name__iexact=name,
            defaults={"name": name},
        )

    target_user.skills.add(skill)
    return JsonResponse({"id": skill.id, "name": skill.name})


@require_POST
@login_required
def skills_remove(request, user_id, skill_id):
    try:
        target_user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return JsonResponse(
            {"status": "error", "detail": "user_not_found"},
            status=HTTPStatus.NOT_FOUND,
        )

    if request.user != target_user and not request.user.is_staff:
        return JsonResponse(
            {"status": "error", "detail": "forbidden"},
            status=HTTPStatus.FORBIDDEN,
        )

    try:
        skill = Skill.objects.get(pk=skill_id)
    except Skill.DoesNotExist:
        return JsonResponse(
            {"status": "error", "detail": "skill_not_found"},
            status=HTTPStatus.NOT_FOUND,
        )

    target_user.skills.remove(skill)
    return JsonResponse({"status": "ok"})