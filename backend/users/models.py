from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ('username', 'first_name', 'last_name')

    username = models.CharField(
        max_length=150,
        unique=True,
    )
    email = models.EmailField(
        max_length=254,
        unique=True,
    )
    first_name = models.CharField(
        max_length=50,
        null=False,
        blank=False,
    )
    last_name = models.CharField(
        max_length=50,
        null=False,
        blank=False,
    )


class Subscription(models.Model):

    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='subscriptions_user',
    )
    author = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='subscriptions_author',
    )
