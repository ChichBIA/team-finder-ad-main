import json
from http import HTTPStatus

from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from team_finder.constants import SKILLS_SEARCH_LIMIT
from team_finder.pagination import (
    DEFAULT_PAGE_NUMBER,
    DEFAULT_PAGE_SIZE,
    build_query_prefix,
    paginate_queryset,
)

from .forms import ProjectForm
from .models import Project, Skill


def project_list(request):
    projects = Project.objects.select_related("owner").prefetch_related("participants")

    page_obj = paginate_queryset(
        projects,
        request.GET.get("page", DEFAULT_PAGE_NUMBER),
        DEFAULT_PAGE_SIZE,
    )

    return render(
        request,
        "projects/project_list.html",
        {
            "projects": page_obj.object_list,
            "page_obj": page_obj,
            "query_prefix": build_query_prefix(),
        },
    )


def project_detail(request, project_id):
    project = get_object_or_404(
        Project.objects.select_related("owner").prefetch_related("participants"),
        pk=project_id,
    )

    return render(
        request,
        "projects/project-details.html",
        {"project": project},
    )


@login_required
def favorite_projects(request):
    projects = request.user.favorites.select_related("owner").prefetch_related("participants")

    page_obj = paginate_queryset(
        projects,
        request.GET.get("page", DEFAULT_PAGE_NUMBER),
        DEFAULT_PAGE_SIZE,
    )

    return render(
        request,
        "projects/favorite_projects.html",
        {
            "projects": page_obj.object_list,
            "page_obj": page_obj,
            "query_prefix": build_query_prefix(),
        },
    )


@login_required
def project_create(request):
    if request.method == "POST":
        form = ProjectForm(request.POST or None)
        if not form.is_valid():
            return render(
                request,
                "projects/create-project.html",
                {"form": form, "is_edit": False},
            )

        project = form.save(commit=False)
        project.owner = request.user
        project.save()
        project.participants.add(request.user)
        return redirect("projects:detail", project_id=project.id)

    form = ProjectForm()

    return render(
        request,
        "projects/create-project.html",
        {"form": form, "is_edit": False},
    )


@login_required
def project_edit(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    if project.owner != request.user and not request.user.is_staff:
        return HttpResponseForbidden("Недостаточно прав")

    if request.method == "POST":
        form = ProjectForm(request.POST or None, instance=project)
        if not form.is_valid():
            return render(
                request,
                "projects/create-project.html",
                {"form": form, "is_edit": True},
            )

        form.save()
        return redirect("projects:detail", project_id=project.id)

    form = ProjectForm(instance=project)

    return render(
        request,
        "projects/create-project.html",
        {"form": form, "is_edit": True},
    )


@require_POST
def toggle_favorite(request, project_id):
    if not request.user.is_authenticated:
        return JsonResponse(
            {"status": "error", "detail": "auth_required"},
            status=HTTPStatus.UNAUTHORIZED,
        )

    try:
        project = Project.objects.get(pk=project_id)
    except Project.DoesNotExist:
        return JsonResponse(
            {"status": "error", "detail": "project_not_found"},
            status=HTTPStatus.NOT_FOUND,
        )

    favorites = request.user.favorites
    if favorites.filter(pk=project.id).exists():
        favorites.remove(project)
        favored = False
    else:
        favorites.add(project)
        favored = True

    return JsonResponse({"status": "ok", "favorited": favored})


@require_POST
@login_required
def toggle_participate(request, project_id):
    try:
        project = Project.objects.get(pk=project_id)
    except Project.DoesNotExist:
        return JsonResponse(
            {"status": "error", "detail": "project_not_found"},
            status=HTTPStatus.NOT_FOUND,
        )

    participants = project.participants
    if participants.filter(pk=request.user.id).exists():
        participants.remove(request.user)
        is_participant = False
    else:
        participants.add(request.user)
        is_participant = True

    return JsonResponse({"status": "ok", "participant": is_participant})


@require_POST
@login_required
def complete_project(request, project_id):
    try:
        project = Project.objects.get(pk=project_id)
    except Project.DoesNotExist:
        return JsonResponse(
            {"status": "error", "detail": "project_not_found"},
            status=HTTPStatus.NOT_FOUND,
        )

    if project.owner != request.user and not request.user.is_staff:
        return JsonResponse(
            {"status": "error", "detail": "forbidden"},
            status=HTTPStatus.FORBIDDEN,
        )

    if project.status != Project.Status.OPEN:
        return JsonResponse(
            {"status": "error", "detail": "project_not_open"},
            status=HTTPStatus.BAD_REQUEST,
        )

    project.status = Project.Status.CLOSED
    project.save(update_fields=["status"])

    return JsonResponse({"status": "ok", "project_status": project.status})


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
def skills_add(request, project_id):
    try:
        project = Project.objects.get(pk=project_id)
    except Project.DoesNotExist:
        return JsonResponse(
            {"status": "error", "detail": "project_not_found"},
            status=HTTPStatus.NOT_FOUND,
        )

    if project.owner != request.user and not request.user.is_staff:
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
            defaults={"name": name}
        )

    project.skills.add(skill)
    return JsonResponse({"id": skill.id, "name": skill.name})


@require_POST
@login_required
def skills_remove(request, project_id, skill_id):
    try:
        project = Project.objects.get(pk=project_id)
    except Project.DoesNotExist:
        return JsonResponse(
            {"status": "error", "detail": "project_not_found"},
            status=HTTPStatus.NOT_FOUND,
        )

    if project.owner != request.user and not request.user.is_staff:
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

    project.skills.remove(skill)
    return JsonResponse({"status": "ok"})