from django.contrib import admin

from .models import (
    Favorite, Ingredient, Recipe, ShoppingCart, Tag
)


class IngredientAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'measurement_unit')
    search_fields = ('name',)


class RecipeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'author', 'text', 'is_favorited')
    list_filter = ('author', 'name', 'tags')

    def is_favorited(self, obj):
        return obj.is_favorited.count()


class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'color', 'slug')
    search_fields = ('name', 'color')


class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('pk', 'user', 'recipe')
    list_filter = ('user', 'recipe')
    search_fields = ('user', 'recipe')


class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('pk', 'user', 'recipe')
    list_filter = ('user', 'recipe')
    search_fields = ('user', 'recipe')


admin.site.register(Tag, TagAdmin)
admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(Recipe, RecipeAdmin)
admin.site.register(Favorite, FavoriteAdmin)
admin.site.register(ShoppingCart, ShoppingCartAdmin)
