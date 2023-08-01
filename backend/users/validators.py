from django.core.exceptions import ValidationError


def validate_username(username):
    if username == 'me':
        raise ValidationError(
            'Нельзя сделать юзернейм "me"'
        )
