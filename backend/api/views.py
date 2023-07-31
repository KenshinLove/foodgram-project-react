from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import (
    DjangoFilterBackend, FilterSet, filters
)
from djoser.views import UserViewSet
from rest_framework import permissions, status
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from api.serializers import (
    IngredientSerializer, RecipeReadSerializer,
    RecipeCreateUpdateSerializer, RecipeForOtherModelsSerializer,
    SubscriptionSerializer, TagSerializer,
    CustomUserCreateSerializer, CustomUserReadSerializer,
)
from recipes.models import (
    Favorite, Ingredient, IngredientsInRecipe,
    Recipe, ShoppingCart, Tag
)
from users.models import Subscription, CustomUser


class CustomPaginator(PageNumberPagination):
    page_size = 6
    page_size_query_param = 'limit'


class CustomFilter(FilterSet):
    tags = filters.AllValuesMultipleFilter(field_name='tags__slug')
    author = filters.ModelChoiceFilter(queryset=CustomUser.objects.all())
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
        if not value or not user.is_authenticated:
            return queryset
        else:
            return queryset.filter(favorites__user=user)

    def get_is_in_shopping_cart(self, queryset, name, value):
        user = self.request.user
        if not value or not user.is_authenticated:
            return queryset
        else:
            return queryset.filter(shopping_cart__user=user)


class IsAuthorOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return (request.method in permissions.SAFE_METHODS
                or obj.author == request.user)


class CustomUserViewSet(UserViewSet):

    http_method_names = ['get', 'post', 'delete']
    pagination_class = CustomPaginator
    permission_classes = (AllowAny, )

    def get_serializer_class(self):
        if (
            self.request.method == 'GET'
            or self.request.method == 'DELETE'
        ):
            return CustomUserReadSerializer
        if self.request.method == 'POST':
            return CustomUserCreateSerializer

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=(IsAuthenticated,)
    )
    def subscribe(self, request, id=None):
        user = request.user
        author = get_object_or_404(CustomUser, id=id)
        subscription = Subscription.objects.filter(
            user=user, author=author
        )
        if request.method == 'DELETE':
            subscription.delete
            return Response(
                'Вы отписались от этого автора',
                status=status.HTTP_204_NO_CONTENT
            )
        if not subscription.exists():
            Subscription.objects.create(
                user=user, author=author
            )
            serializer = SubscriptionSerializer(
                author,
                context={'request': request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response('Вы уже подписаны на этого автора')

    @action(
        detail=False,
        methods=['get'],
        permission_classes=(IsAuthenticated,),
        pagination_class=CustomPaginator
    )
    def subscriptions(self, request):
        user = request.user
        queryset = CustomUser.objects.filter(subscriptions_author__user=user)
        pages = self.paginate_queryset(queryset)
        serializer = SubscriptionSerializer(
            pages, many=True, context={'request': request}
        )
        return self.get_paginated_response(serializer.data)


class IngredientViewSet(ModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (SearchFilter,)
    search_fields = ['name', ]


class TagViewSet(ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class RecipeViewSet(ModelViewSet):

    queryset = Recipe.objects.all()
    http_method_names = ['get', 'post', 'patch', 'delete']
    permission_classes = [IsAuthorOrReadOnly, ]
    pagination_class = CustomPaginator
    filter_backends = [DjangoFilterBackend, ]
    filterset_class = CustomFilter

    def get_serializer_class(self):
        if (
            self.request.method == 'GET'
            or self.request.method == 'DELETE'
        ):
            return RecipeReadSerializer
        if (
            self.request.method == 'POST'
            or self.request.method == 'PATCH'
        ):
            return RecipeCreateUpdateSerializer

    @action(detail=True, methods=['post', 'delete'],
            permission_classes=[IsAuthenticated, ])
    def favorite(self, request, pk):
        user = request.user
        recipe = get_object_or_404(Recipe, pk=pk)
        favorite = Favorite.objects.filter(user=user, recipe=recipe)
        if request.method == 'DELETE':
            favorite.delete()
            return Response(
                'Рецепт удален из избранного',
                status=status.HTTP_204_NO_CONTENT
            )
        if not favorite.exists():
            Favorite.objects.create(
                user=user, recipe=recipe
            )
            serializer = RecipeForOtherModelsSerializer(
                recipe, context={'request': request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response('Этот рецепт уже есть в избранном')

    @action(detail=True, methods=['post', 'delete'],
            permission_classes=[IsAuthenticated, ])
    def shopping_cart(self, request, pk):
        user = request.user
        recipe = get_object_or_404(Recipe, pk=pk)
        shopping_cart = ShoppingCart.objects.filter(user=user, recipe=recipe)
        if request.method == 'DELETE':
            shopping_cart.delete()
            return Response(
                'Рецепт удален из корзины',
                status=status.HTTP_204_NO_CONTENT
            )
        if not shopping_cart.exists():
            ShoppingCart.objects.create(
                user=user, recipe=recipe
            )
            serializer = RecipeForOtherModelsSerializer(
                recipe, context={'request': request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response('Этот рецепт уже в корзине')

    @action(
        detail=False,
        methods=('GET',),
        permission_classes=[IsAuthenticated]
    )
    def download_shopping_cart(self, request):
        user = request.user
        ingredients = (
            IngredientsInRecipe.objects
            .filter(recipe__shopping_cart__user=user)
            .values('ingredient__name', 'ingredient__measurement_unit',)
            .annotate(total_amount=Sum('amount'))
        )
        shopping_list = ["Список покупок\n\n"]
        for ingredient in ingredients:
            amount = ingredient['total_amount']
            name = ingredient['ingredient__name']
            measurement_unit = ingredient['ingredient__measurement_unit']
            shopping_list.append(
                f'{name} - {amount} {measurement_unit}.\n'
            )

        return HttpResponse(
            shopping_list,
            {
                "Content-Type": "text/plain",
                "Content-Disposition": "attachment; filename='shop_list.txt'",
            },
        )
