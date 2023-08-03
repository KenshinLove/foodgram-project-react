from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from drf_extra_fields.fields import Base64ImageField
from rest_framework.serializers import (
    CharField, ModelSerializer, PrimaryKeyRelatedField,
    ReadOnlyField, SerializerMethodField, ValidationError
)

from recipes.models import (
    Favorite, Ingredient, IngredientsInRecipe,
    Recipe, ShoppingCart, Tag
)
from users.models import Subscription

CustomUser = get_user_model()


class CustomUserReadSerializer(ModelSerializer):
    is_subscribed = SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = (
            'id', 'username', 'email', 'first_name',
            'last_name', 'is_subscribed'
        )

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        return (request and request.user.is_authenticated
                and request.user.subscriptions_user.filter(
                    author=obj
                ).exists())


class CustomUserCreateSerializer(ModelSerializer):

    password = CharField(write_only=True)

    class Meta:
        model = CustomUser
        fields = (
            'id', 'username', 'email', 'first_name',
            'last_name', 'password'
        )

    def validate_password(self, password):
        password = make_password(password)
        return password


class SubscriptionReadSerializer(ModelSerializer):

    is_subscribed = SerializerMethodField()
    recipes = SerializerMethodField()
    recipes_count = SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = (
            'id', 'email', 'username', 'first_name', 'last_name',
            'recipes', 'recipes_count', 'is_subscribed'
        )

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        return (request and request.user.is_authenticated
                and request.user.subscriptions_user.filter(
                    author=obj
                ).exists())

    def get_recipes(self, obj):
        request = self.context.get('request')
        limit = request.GET.get('recipes_limit')
        recipes = obj.recipes.all()
        if limit:
            recipes = recipes[:int(limit)]
        serializer = RecipeForOtherModelsSerializer(
            recipes,
            many=True,
            read_only=True,
        )
        return serializer.data

    def get_recipes_count(self, obj):
        return obj.recipes.count()


class SubscriptionCreateSerializer(ModelSerializer):

    class Meta:
        model = Subscription
        fields = ('user', 'author')

    def validate(self, data):
        user = data.get('user')
        author = data.get('author')
        if user == author:
            raise ValidationError(
                'Нельзя подписаться на себя'
            )
        if Subscription.objects.filter(user=user, author=author).exists():
            raise ValidationError(
                'Нельзя подписаться два раза'
            )
        return data


class IngredientSerializer(ModelSerializer):

    class Meta:
        model = Ingredient
        fields = '__all__'


class TagSerializer(ModelSerializer):

    class Meta:
        model = Tag
        fields = '__all__'


class IngredientsInRecipeReadSerializer(ModelSerializer):

    id = ReadOnlyField(source='ingredient.id')
    name = ReadOnlyField(source='ingredient.name')
    measurement_unit = ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = IngredientsInRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount')


class IngredientsInRecipeCreateSerializer(ModelSerializer):

    id = PrimaryKeyRelatedField(queryset=Ingredient.objects.all())

    class Meta:
        model = IngredientsInRecipe
        fields = ('id', 'amount')


class RecipeReadSerializer(ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    author = CustomUserReadSerializer(read_only=True)
    ingredients = IngredientsInRecipeReadSerializer(
        many=True, read_only=True, source='ingredients_list'
    )
    image = Base64ImageField()
    is_favorited = SerializerMethodField()
    is_in_shopping_cart = SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients', 'is_favorited',
            'is_in_shopping_cart', 'name', 'image', 'text',
            'cooking_time'
        )

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        return (request and request.user.is_authenticated
                and request.user.favorites.filter(recipe=obj).exists())

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        return (request and request.user.is_authenticated
                and request.user.shopping_cart.filter(recipe=obj).exists())


class RecipeCreateUpdateSerializer(ModelSerializer):

    tags = PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True,
    )
    author = CustomUserReadSerializer(read_only=True)
    ingredients = IngredientsInRecipeCreateSerializer(many=True)
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'name', 'author', 'tags', 'ingredients',
            'text', 'image', 'cooking_time',
        )

    def create(self, validated_data):
        author = self.context.get('request').user
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(author=author, **validated_data)
        self.get_ingredient_list(recipe, ingredients)
        recipe.tags.set(tags)
        return recipe

    def update(self, recipe, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe = super().update(recipe, validated_data)
        recipe.tags.clear()
        recipe.tags.set(tags)
        recipe.ingredients.clear()
        self.get_ingredient_list(recipe, ingredients)
        return recipe

    def get_ingredient_list(self, recipe, ingredients):
        ingr_list = []
        for item in ingredients:
            ingr_list.append(IngredientsInRecipe(
                recipe=recipe,
                ingredient=item['id'],
                amount=item['amount']
            ))
        IngredientsInRecipe.objects.bulk_create(ingr_list)

    def to_representation(self, recipe):
        return RecipeReadSerializer(recipe, context=self.context).data


class RecipeForOtherModelsSerializer(ModelSerializer):

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class FavoriteSerializer(ModelSerializer):

    class Meta:
        model = Favorite
        fields = '__all__'

    def validate(self, data):
        user = data.get('user')
        recipe = data.get('recipe')
        if Favorite.objects.filter(user=user, recipe=recipe).exists():
            raise ValidationError(
                'Нельзя добавить рецепт два раза'
            )
        return data


class ShoppingCartSerializer(ModelSerializer):

    class Meta:
        model = ShoppingCart
        fields = '__all__'

    def validate(self, data):
        user = data.get('user')
        recipe = data.get('recipe')
        if ShoppingCart.objects.filter(user=user, recipe=recipe).exists():
            raise ValidationError(
                'Нельзя добавить рецепт два раза'
            )
        return data
