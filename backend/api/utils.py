from django.contrib.auth import get_user_model
from django_filters.rest_framework import FilterSet, filters
from rest_framework import permissions
from rest_framework.pagination import PageNumberPagination

from backend.settings import RECIPESR_ON_PAGE
from recipes.models import Recipe

CustomUser = get_user_model()


class RecipesLimitPaginator(PageNumberPagination):
    page_size = RECIPESR_ON_PAGE
    page_size_query_param = 'limit'


class RecipesFilter(FilterSet):
    tags = filters.AllValuesMultipleFilter(field_name='tags__slug')
    is_in_favorite = filters.BooleanFilter(method='get_is_in_favorite')
    is_in_shopping_cart = filters.BooleanFilter(
        method='get_is_in_shopping_cart'
    )

    class Meta:
        model = Recipe
        fields = (
            'tags',
            'author',
            'is_in_favorite',
            'is_in_shopping_cart',
        )

    def get_is_in_favorite(self, queryset, name, value):
        user = self.request.user
        if value and user.is_authenticated:
            return queryset.filter(favorites__user=user)
        return queryset

    def get_is_in_shopping_cart(self, queryset, name, value):
        user = self.request.user
        if value and user.is_authenticated:
            return queryset.filter(shopping_cart__user=user)
        return queryset


class IsAuthorOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return (request.method in permissions.SAFE_METHODS
                or obj.author == request.user)
