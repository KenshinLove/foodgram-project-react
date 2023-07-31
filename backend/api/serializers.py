import base64

from django.core.files.base import ContentFile
from rest_framework.serializers import (
    CharField, ImageField, ModelSerializer,
    PrimaryKeyRelatedField, ReadOnlyField, SerializerMethodField
)
from recipes.models import (
    Favorite, Ingredient, IngredientsInRecipe,
    Recipe, ShoppingCart, Tag
)
from users.models import CustomUser, Subscription


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
        if request is not None:
            user = request.user
            if user.is_authenticated:
                return Subscription.objects.filter(user=user,
                                                   author=obj).exists()
        return False


class CustomUserCreateSerializer(ModelSerializer):

    password = CharField()

    class Meta:
        model = CustomUser
        fields = (
            'id', 'username', 'email', 'first_name',
            'last_name', 'password'
        )


class SubscriptionSerializer(ModelSerializer):

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
        author = obj
        if not request.user.is_authenticated:
            return False
        else:
            return Subscription.objects.filter(
                author=author, user=request.user
            ).exists()

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


class Base64ImageField(ImageField):

    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)
        return super().to_internal_value(data)


class RecipeReadSerializer(ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    author = CustomUserReadSerializer(read_only=True)
    ingredients = IngredientsInRecipeReadSerializer(
        many=True, read_only=True, source='ingredients_list'
    )
    image = Base64ImageField(required=False, allow_null=True)
    is_in_favorite = SerializerMethodField()
    is_in_shopping_cart = SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients', 'is_in_favorite',
            'is_in_shopping_cart', 'name', 'image', 'text',
            'cooking_time'
        )

    def get_is_in_favorite(self, obj):
        request = self.context.get('request')
        if request is not None:
            user = request.user
            if user.is_authenticated:
                return Favorite.objects.filter(user=user,
                                               recipe=obj).exists()
        return False

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if request is not None:
            user = request.user
            if user.is_authenticated:
                return ShoppingCart.objects.filter(user=user,
                                                   recipe=obj).exists()
        return False


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
        ingr_list = []
        for item in ingredients:
            ingr_list.append(IngredientsInRecipe(
                recipe=recipe,
                ingredient=item['id'],
                amount=item['amount']
            ))
            IngredientsInRecipe.objects.bulk_create(ingr_list)
        recipe.tags.set(tags)
        return recipe

    def update(self, recipe, validated_data):
        if validated_data.get('image') is not None:
            recipe.image = validated_data.pop('image')
        recipe.name = validated_data.get('name')
        recipe.text = validated_data.get('text')
        recipe.cooking_time = validated_data.get('cooking_time')
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe.tags.set(tags)
        IngredientsInRecipe.objects.filter(recipe=recipe).delete()
        ingr_list = []
        for item in ingredients:
            ingr_list.append(IngredientsInRecipe(
                recipe=recipe,
                ingredient=item['id'],
                amount=item['amount']
            ))
            IngredientsInRecipe.objects.bulk_create(ingr_list)
        recipe.save()
        return recipe

    def to_representation(self, recipe):
        return RecipeReadSerializer(recipe, context=self.context).data


class RecipeForOtherModelsSerializer(ModelSerializer):

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class FavoriteSerializer(ModelSerializer):

    recipe = PrimaryKeyRelatedField(
        queryset=Recipe.objects.all()
    )
    user = PrimaryKeyRelatedField(
        queryset=CustomUser.objects.all()
    )

    class Meta:
        model = Favorite
        fields = '__all__'


class ShoppingCartSerializer(ModelSerializer):

    recipe = PrimaryKeyRelatedField(
        queryset=Recipe.objects.all()
    )
    user = PrimaryKeyRelatedField(
        queryset=CustomUser.objects.all()
    )

    class Meta:
        model = ShoppingCart
        fields = '__all__'
