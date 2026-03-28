from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import login_required
from .models import sync_profile_role


def role_required(*roles):
    def decorator(view_func):
        @login_required
        def _wrapped(request, *args, **kwargs):
            profile = sync_profile_role(request.user)
            if profile.role not in roles:
                raise PermissionDenied
            return view_func(request, *args, **kwargs)
        return _wrapped
    return decorator
