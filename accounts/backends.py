from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend


class EmailBackend(ModelBackend):
    """Sign in with an email address and password."""

    def authenticate(self, request, username=None, password=None, **kwargs):
        User = get_user_model()
        if username is None:
            username = kwargs.get(User.USERNAME_FIELD)
        if not username or password is None:
            return None

        for user in User.objects.filter(email__iexact=username.strip()):
            if user.check_password(password) and self.user_can_authenticate(user):
                return user

        User().set_password(password)  # keeps timing similar when no user matches
        return None
