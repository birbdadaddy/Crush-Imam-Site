from allauth.account.signals import user_signed_up
from django.dispatch import receiver
from django.contrib.auth import login


@receiver(user_signed_up)
def login_user_on_signup(request, user, **kwargs):
    """Automatically log the user in immediately after successful signup."""
    try:
        # `request` is provided by allauth signal
        login(request, user)
    except Exception:
        # fail silently — signup still succeeds
        pass
