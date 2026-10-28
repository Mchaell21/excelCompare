from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied


def user_has_role(user, *role_names):
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    role_set = {g.name for g in user.groups.all()}
    return bool(set(role_names) & role_set)


def role_required(*role_names):
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped(request, *args, **kwargs):
            if not user_has_role(request.user, *role_names):
                raise PermissionDenied
            return view_func(request, *args, **kwargs)
        return _wrapped
    return decorator


def is_sales_admin(user):
    return user_has_role(user, 'Sales Admin')


def is_dispatch(user):
    return user_has_role(user, 'Dispatch')

def is_manager(user):
    return user_has_role(user, 'Manager')

def is_accounting(user):
    return user_has_role(user, 'Accounting')

def superuser_required(view_func):
    @wraps(view_func)
    @login_required
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_superuser:
            raise PermissionDenied
        return view_func(request, *args, **kwargs)
    return _wrapped
