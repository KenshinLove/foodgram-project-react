from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response

from api.serializers import RecipeForOtherModelsSerializer
from recipes.models import Recipe


def add_delete_recipe(serializer, pk, request, model):
    user = request.user
    recipe = get_object_or_404(Recipe, pk=pk)
    object = model.objects.filter(user=user, recipe=recipe)
    if request.method == 'DELETE':
        object.delete()
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
