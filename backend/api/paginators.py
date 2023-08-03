from django.conf import settings
from rest_framework.pagination import PageNumberPagination


class RecipesLimitPaginator(PageNumberPagination):
    page_size = settings.RECIPESR_ON_PAGE
    page_size_query_param = 'limit'
