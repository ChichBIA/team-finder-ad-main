from django.core.paginator import Paginator

from .constants import DEFAULT_PAGE_NUMBER, DEFAULT_PAGE_SIZE


def paginate_queryset(queryset, page_number, per_page=DEFAULT_PAGE_SIZE):
    paginator = Paginator(queryset, per_page)
    page = page_number or DEFAULT_PAGE_NUMBER
    return paginator.get_page(page)


def build_query_prefix(**params):
    parts = []
    for key, value in params.items():
        if value not in (None, ""):
            parts.append(f"{key}={value}&")
    return "".join(parts)
