# django-rest-framework-guardian

[![build-status](https://github.com/rpkilby/django-rest-framework-guardian/actions/workflows/main.yml/badge.svg)](https://github.com/rpkilby/django-rest-framework-guardian/actions/workflows/main.yml)
[![codecov](https://codecov.io/gh/rpkilby/django-rest-framework-guardian/graph/badge.svg)](https://codecov.io/gh/rpkilby/django-rest-framework-guardian)
[![License](https://img.shields.io/pypi/l/djangorestframework-guardian.svg)](https://pypi.org/project/djangorestframework-guardian)
[![Version](https://img.shields.io/pypi/v/djangorestframework-guardian.svg)](https://pypi.org/project/djangorestframework-guardian)
[![Python](https://img.shields.io/pypi/pyversions/djangorestframework-guardian.svg)](https://pypi.org/project/djangorestframework-guardian/)

django-rest-framework-guardian provides django-guardian integrations for Django REST Framework.


## Installation & Setup

To use django-rest-framework-guardian, install it into your environment.

```sh
$ pip install djangorestframework-guardian
```

Ensure both Django REST Framework and django-guardian are configured and added to your `INSTALLED_APPS` setting.

```python
INSTALLED_APPS = [
    'rest_framework',
    'guardian',
]

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'guardian.backends.ObjectPermissionBackend',
]
```


## ObjectPermissionsFilter

The filter will ensure that querysets only returns objects for which the user has the appropriate view permission.

If you're using `ObjectPermissionsFilter`, you'll probably also want to add an appropriate object permissions
class, to ensure that users can only operate on instances if they have the appropriate object permissions.  The easiest
way to do this is to subclass `DjangoObjectPermissions` and add `'view'` permissions to the `perms_map` attribute.

An example using both `ObjectPermissionsFilter` and `DjangoObjectPermissions` might look like the following:

**permissions.py**:

```python
from rest_framework import permissions


class CustomObjectPermissions(permissions.DjangoObjectPermissions):
    """
    Similar to `DjangoObjectPermissions`, but adding 'view' permissions.
    """
    perms_map = {
        'GET': ['%(app_label)s.view_%(model_name)s'],
        'OPTIONS': ['%(app_label)s.view_%(model_name)s'],
        'HEAD': ['%(app_label)s.view_%(model_name)s'],
        'POST': ['%(app_label)s.add_%(model_name)s'],
        'PUT': ['%(app_label)s.change_%(model_name)s'],
        'PATCH': ['%(app_label)s.change_%(model_name)s'],
        'DELETE': ['%(app_label)s.delete_%(model_name)s'],
    }
```

**views.py**:

```python
from rest_framework import viewsets
from rest_framework_guardian import filters

from myapp.models import Event
from myapp.permissions import CustomObjectPermissions
from myapp.serializers import EventSerializer


class EventViewSet(viewsets.ModelViewSet):
    """
    Viewset that only lists events if user has 'view' permissions, and only
    allows operations on individual events if user has appropriate 'view', 'add',
    'change' or 'delete' permissions.
    """
    queryset = Event.objects.all()
    serializer_class = EventSerializer
    permission_classes = [CustomObjectPermissions]
    filter_backends = [filters.ObjectPermissionsFilter]
```


## ObjectPermissionsAssignmentMixin

A serializer mixin that allows permissions to be easily assigned to users and/or groups.
So each time an object is created or updated, the `permissions_map` returned by `Serializer.get_permissions_map` will be used to assign permission(s) to that object.

Please note that the existing permissions will remain intact.

A usage example might look like the following:

```python
from rest_framework_guardian.serializers import ObjectPermissionsAssignmentMixin

from blog.models import Post


class PostSerializer(ObjectPermissionsAssignmentMixin, serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = '__all__'

    def get_permissions_map(self, created):
        current_user = self.context['request'].user
        readers = Group.objects.get(name='readers')
        supervisors = Group.objects.get(name='supervisors')

        return {
            'view_post': [current_user, readers],
            'change_post': [current_user],
            'delete_post': [current_user, supervisors]
        }

```


## Release Process

- Update changelog
- Update package version in setup.py
- Create git tag for version
- Build & upload release to PyPI
  ```bash
  $ pip install -U setuptools build twine
  $ rm -rf dist/
  $ python -m build
  $ twine upload -r test dist/*
  $ twine upload dist/*
  ```

## License

See: [LICENSE](https://github.com/rpkilby/django-rest-framework-guardian/blob/master/LICENSE)
