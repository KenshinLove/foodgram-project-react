from django.db import models

from users.models import CustomUser


class Ingredient (models.Model):
    name = models.CharField(
        max_length=256,
    )
    measurement_unit = models.CharField(
        max_length=16,
    )


class Tag(models.Model):
    name = models.CharField(
        max_length=50,
        unique=True,
    )
    color = models.CharField(
        max_length=7,
        unique=True,
    )
    slug = models.SlugField(
        max_length=50,
        unique=True,
    )


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
    )
    tags = models.ManyToManyField(
        Tag,
        related_name='recipes',
    )
    cooking_time = models.IntegerField()


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
    amount = models.IntegerField()


class Favorite(models.Model):
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='favorites',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorites',
    )


class ShoppingCart(models.Model):
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='shopping_cart',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='shopping_cart',
    )
