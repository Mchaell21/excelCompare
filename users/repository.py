from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.models import Group

from .models import Advanced

class UserRepository:
    def get_user_model(self):
        return get_user_model()

    def get_by_username(self, username):
        try:
            return Advanced.objects.get(username=username)
        except Advanced.DoesNotExist:
            return None

    def get_by_id(self, user_id):
        User = self.get_user_model()
        try:
            return User.objects.get(id=user_id)
        except (User.DoesNotExist, ValueError):
            return None

    def list_users(self):
        return (
            Advanced.objects
            .prefetch_related('groups')
            .order_by('-is_superuser', '-is_active', 'username')
        )

    def authenticate(self, request, username, password):
        return authenticate(request, username=username, password=password)

    def create_user(self, *, username, password, first_name='',
                    last_name='', role=''):
        User = self.get_user_model()
        user = User.objects.create_user(
            username=username,
            password=password,
            first_name=first_name,
            last_name=last_name,
        )

        # print('role')
        # print(role)
        self.set_role(user, role)
        return user

    def set_role(self, user, role):
        user.groups.clear()
        if role:
            group, _ = Group.objects.get_or_create(name=role)
            # print(group, role)
            user.groups.add(group)
        return user

    def set_active(self, user, is_active):
        user.is_active = bool(is_active)
        user.save(update_fields=['is_active'])
        return user

    def set_password(self, user, raw_password):
        user.set_password(raw_password)
        user.save(update_fields=['password'])
        return user
