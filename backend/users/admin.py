from django.contrib import admin

from .models import CustomUser, Subscription


class CustomUserAdmin(admin.ModelAdmin):
    list_display = (
        'username', 'email', 'first_name', 'last_name',
    )
    search_fields = ('username',)
    empty_value_display = '-пусто-'


class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'author',)
    list_filter = ('user', 'author',)
    search_fields = ('user', 'author',)
    empty_value_display = '-пусто-'


admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Subscription, SubscriptionAdmin)
