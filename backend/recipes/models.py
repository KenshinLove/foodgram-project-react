from colorfield.fields import ColorField
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db import models

CustomUser = get_user_model()


class Ingredient (models.Model):
    name = models.CharField(
        max_length=256,
    )
    measurement_unit = models.CharField(
        max_length=16,
    )

    class Meta:
        ordering = ('name', )


class Tag(models.Model):
    name = models.CharField(
        max_length=settings.TAG_MAX_LENGTH,
        unique=True,
    )
    color = ColorField(
        unique=True,
    )
    slug = models.SlugField(
        max_length=settings.TAG_MAX_LENGTH,
        unique=True,
    )

    class Meta:
        ordering = ('name', )


class Recipe(models.Model):
    author = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='recipes',
    )
    name = models.CharField(
        max_length=200,
    )
    image = models.ImageField(
        upload_to='images/',
    )
    text = models.TextField()
    ingredients = models.ManyToManyField(
        Ingredient,
        related_name='recipes',
        through='IngredientsInRecipe'
    )
    tags = models.ManyToManyField(
        Tag,
        related_name='recipes',
    )
    cooking_time = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1)],
    )
    pub_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-pub_date', )


class IngredientsInRecipe(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='ingredients_list',
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='ingredients_list',
    )
    amount = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1)],
    )

    class Meta:
        ordering = ('recipe', )
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='unique_ingredients'
            )
        ]


class Favorite(models.Model):
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
    )

    class Meta:
        ordering = ('user', )
        default_related_name = 'favorites'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_favorite'
            )
        ]


class ShoppingCart(models.Model):
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
    )

    class Meta:
        ordering = ('user', )
        default_related_name = 'shopping_cart'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_shopping_cart'
            )
        ]
