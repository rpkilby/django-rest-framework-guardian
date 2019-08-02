import warnings

from rest_framework.filters import BaseFilterBackend


class ObjectPermissionsFilter(BaseFilterBackend):
    """
    A filter backend that limits results to those where the requesting user
    has read object level permissions.
    """
    perm_format = '%(app_label)s.view_%(model_name)s'
    shortcut_kwargs = {
        'accept_global_perms': False,
    }

    def filter_queryset(self, request, queryset, view):
        # We want to defer this import until runtime, rather than import-time.
        # See https://github.com/encode/django-rest-framework/issues/4608
        # (Also see #1624 for why we need to make this import explicitly)
        from guardian.shortcuts import get_objects_for_user

        user = request.user
        permission = self.perm_format % {
            'app_label': queryset.model._meta.app_label,
            'model_name': queryset.model._meta.model_name,
        }

        return get_objects_for_user(
            user, permission, queryset,
            **self.shortcut_kwargs)


class DjangoObjectPermissionsFilter(ObjectPermissionsFilter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        warnings.warn(
            '`DjangoObjectPermissionsFilter` has been renamed to '
            '`ObjectPermissionsFilter` and will be removed in the future.',
            DeprecationWarning, stacklevel=2,
        )
