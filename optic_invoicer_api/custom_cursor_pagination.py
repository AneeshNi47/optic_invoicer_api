from rest_framework.pagination import CursorPagination, _positive_int
from rest_framework.settings import api_settings


class CustomCursorPagination(CursorPagination):
    page_size = api_settings.PAGE_SIZE
    ordering = '-created_on'
    page_size_query_param = 'page_size'  # This allows the client to set the page size

    def get_page_size(self, request):
        if self.page_size_query_param:
            try:
                return _positive_int(
                    request.query_params[self.page_size_query_param],
                    strict=True,
                    cutoff=self.max_page_size
                )
            except (KeyError, ValueError):
                pass

        return self.page_size
