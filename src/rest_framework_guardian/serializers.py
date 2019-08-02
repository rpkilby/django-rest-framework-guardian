from collections.abc import Mapping

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db import transaction
from rest_framework.serializers import Serializer


User = get_user_model()


class ObjectPermissionsAssignmentMixin(Serializer):
    """
    A serializer mixin that provides an easy way to assign permissions
    to given users and/or group when an object is created or updated.
    """

    def save(self, **kwargs):
        created = self.instance is not None

        result = super().save(**kwargs)

        permissions_map = self.get_permissions_map(created)
        self.assign_permissions(permissions_map)

        return result

    def get_permissions_map(self, created):
        """
        Return a map where keys are permissions
        and values are list of users and/or groups
        """
        raise NotImplementedError

    def assign_permissions(self, permissions_map):
        """
        Assign the permissions to their associated users/groups.
        """
        # Import at runtime (see: DjangoObjectPermissionsFilter.filter_queryset)
        from guardian.shortcuts import assign_perm

        assert isinstance(permissions_map, Mapping), (
            'Expected %s.get_permissions_map to return a dict, got %s instead.'
            % (self.__class__.__name__, type(permissions_map).__name__)
        )

        with transaction.atomic():
            for permission, assignees in permissions_map.items():
                users = [u for u in assignees if isinstance(u, User)]
                groups = [g for g in assignees if isinstance(g, Group)]

                # TODO: support Django Guardian bulk permission assigning
                # Currently, trying to assign a permission to multiple
                # users or groups can result uniqueness constraint error
                # in database level due to `assign_perm` not checking
                # the existance of a permission before inserting
                for user in users:
                    assign_perm(permission, user, self.instance)
                for group in groups:
                    assign_perm(permission, group, self.instance)
