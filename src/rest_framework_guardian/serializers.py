from collections import Mapping

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db import transaction
from rest_framework.serializers import Serializer


User = get_user_model()


class DjangoGuardianObjectPermissionsAssigner(Serializer):
    """
    A serializer mixin that provides an easy way to assign permissions
    to given users and/or group when an object is created or updated.
    """

    def __init__(self, *args, **kwargs):
        super(DjangoGuardianObjectPermissionsAssigner, self).__init__(
            *args,
            **kwargs,
        )

        assert 'guardian' in settings.INSTALLED_APPS, (
            'Using DjangoGuardianObjectPermAssigner, '
            'but django-guardian is not installed.'
        )

    def get_permissions_map(self, created):
        """
        Return a map where keys are permissions
        and values are list of users and/or groups
        """
        return {}

    def save(self, **kwargs):
        created = self.instance is not None

        super(DjangoGuardianObjectPermissionsAssigner, self).save(**kwargs)

        self._handle_permissions(created)

        return self.instance

    def _handle_permissions(self, created):
        permissions_map = self.get_permissions_map(
            False,
        )
        assert isinstance(permissions_map, Mapping), (
            '%s.get_permissions_map is expected '
            'to return an Mapping (e.g. dict), got %r instead' % (
                self.__class__.__name__,
                type(permissions_map).__name__,
            )
        )

        with transaction.atomic():
            self._assign_permissions(
                permissions_map,
            )

    def _assign_permissions(self, permissions_map):
        from guardian.shortcuts import assign_perm

        for permission, users_or_groups in permissions_map.items():
            users = [
                user_or_group
                for user_or_group in users_or_groups
                if isinstance(user_or_group, User)
            ]
            groups = [
                user_or_group
                for user_or_group in users_or_groups
                if isinstance(user_or_group, Group)
            ]

            # TODO: support Django Guardian bulk permission assigning
            # Currently, trying to assign a permission to multiple
            # users or groups can result uniqueness constraint error
            # in database level due to `assign_perm` not checking
            # the existance of a permission before inserting
            for user in users:
                assign_perm(permission, user, self.instance)
            for group in groups:
                assign_perm(permission, group, self.instance)