from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from api.serializers import (
    FavoriteSerializer, IngredientSerializer, RecipeReadSerializer,
    RecipeCreateUpdateSerializer, RecipeForOtherModelsSerializer, ShoppingCartSerializer,
    SubscriptionCreateSerializer, SubscriptionReadSerializer, TagSerializer,
)
from api.filters import RecipesFilter
from api.paginators import RecipesLimitPaginator
from api.permissions import IsAuthorOrReadOnly
from recipes.models import (
    Favorite, Ingredient, IngredientsInRecipe,
    Recipe, ShoppingCart, Tag
)
from users.models import Subscription

CustomUser = get_user_model()


class CustomUserViewSet(UserViewSet):

    http_method_names = ('get', 'post', 'delete')
    pagination_class = RecipesLimitPaginator
    permission_classes = (AllowAny, )

    @action(
        detail=True,
        methods=('post', 'delete'),
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
        data = {'user': user.id, 'author': author.id}
        create_serializer = SubscriptionCreateSerializer(
            data=data,
            context={'request': request}
        )
        create_serializer.is_valid()
        create_serializer.save()
        read_serializer = SubscriptionReadSerializer(
            author,
            context={'request': request}
        )
        return Response(read_serializer.data, status=status.HTTP_201_CREATED)

    @action(
        detail=False,
        methods=['get'],
        permission_classes=(IsAuthenticated,),
        pagination_class=RecipesLimitPaginator
    )
    def subscriptions(self, request):
        user = request.user
        queryset = CustomUser.objects.filter(subscriptions_author__user=user)
        pages = self.paginate_queryset(queryset)
        serializer = SubscriptionReadSerializer(
            pages, many=True, context={'request': request}
        )
        return self.get_paginated_response(serializer.data)


class IngredientViewSet(ModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (SearchFilter,)
    search_fields = ('name', )


class TagViewSet(ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class RecipeViewSet(ModelViewSet):

    queryset = Recipe.objects.all()
    http_method_names = ('get', 'post', 'patch', 'delete')
    permission_classes = (IsAuthorOrReadOnly, )
    pagination_class = RecipesLimitPaginator
    filter_backends = (DjangoFilterBackend, )
    filterset_class = RecipesFilter

    def get_serializer_class(self):
        if self.request.method in ('GET', 'DELETE'):
            return RecipeReadSerializer
        return RecipeCreateUpdateSerializer
    
    def add_delete_recipe(self, serializer, pk, request, model):
        user = request.user
        recipe = get_object_or_404(Recipe, pk=pk)
        object = model.objects.filter(user=user, recipe=recipe)
        if request.method == 'DELETE':
            delete = object.delete()
            if delete[0]==0:
                return Response(
                    'Такого рецепта нет',
                    status=status.HTTP_400_BAD_REQUEST
                )
            return Response(
                'Рецепт удален из корзины',
                status=status.HTTP_204_NO_CONTENT
            )
        data = {'user': user.id, 'recipe': recipe.id}
        create_serializer = serializer(
            data=data,
            context={'request': request}
        )
        create_serializer.is_valid()
        create_serializer.save()
        read_serializer = RecipeForOtherModelsSerializer(
            recipe,
            context={'request': request}
        )
        return Response(read_serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post', 'delete'],
            permission_classes=[IsAuthenticated, ])
    def favorite(self, request, pk):
        serializer = FavoriteSerializer
        model = Favorite
        return self.add_delete_recipe(serializer, pk, request, model)

    @action(detail=True, methods=['post', 'delete'],
            permission_classes=[IsAuthenticated, ])
    def shopping_cart(self, request, pk):
        serializer = ShoppingCartSerializer
        model = ShoppingCart
        return self.add_delete_recipe(serializer, pk, request, model)

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
            .order_by('ingredient__name')
        )
        return self.print_shopping_list_txt_file(ingredients)

    def print_shopping_list_txt_file(self, ingredients):
        shopping_list = ['Список покупок\n\n']
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
