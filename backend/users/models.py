from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models

from backend.settings import MAX_LENGTH
from .validators import validate_username


class CustomUser(AbstractUser):

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ('username', 'first_name', 'last_name')

    username = models.CharField(
        max_length=150,
        unique=True,
        validators=(UnicodeUsernameValidator(), validate_username),
    )
    email = models.EmailField(
        max_length=254,
        unique=True,
    )
    first_name = models.CharField(
        null=False,
        blank=False,
        max_length=MAX_LENGTH
    )
    last_name = models.CharField(
        null=False,
        blank=False,
        max_length=MAX_LENGTH
    )

    class Meta:
        ordering = ('username', )


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

    class Meta:
        ordering = ('user', )
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'],
                name='unique_subscription'
            )
        ]
