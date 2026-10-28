from users.decorators import is_dispatch, is_sales_admin, is_manager, is_accounting

def user_roles(request):
    user = request.user
    authenticated = bool(user and user.is_authenticated)
    return {
        'is_sales_admin': authenticated and is_sales_admin(user),
        'is_dispatch': authenticated and is_dispatch(user),
        'is_staff_user': authenticated and (
            user.is_superuser or is_sales_admin(user) or is_dispatch(user)),
        'is_manager': authenticated and is_manager(user),
        'is_accounting': authenticated and is_accounting(user)
    }
