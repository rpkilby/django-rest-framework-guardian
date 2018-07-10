# django-rest-framework-guardian

[![Build Status](https://travis-ci.org/rpkilby/django-rest-framework-guardian.svg?branch=master)](https://travis-ci.org/rpkilby/django-rest-framework-guardian)
[![Codecov](https://codecov.io/gh/rpkilby/django-rest-framework-guardian/branch/master/graph/badge.svg)](https://codecov.io/gh/rpkilby/django-rest-framework-guardian)
[![Version](https://img.shields.io/pypi/v/djangorestframework-guardian.svg)](https://pypi.org/project/djangorestframework-guardian)
[![License](https://img.shields.io/pypi/l/djangorestframework-guardian.svg)](https://pypi.org/project/djangorestframework-guardian)

django-rest-framework-guardian provides django-guardian integrations for Django REST Framework.
Currently, this is only includes the `DjangoObjectPermissionsFilter`.


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

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'guardian.backends.ObjectPermissionBackend',
)
```


## DjangoObjectPermissionsFilter

The filter will ensure that querysets only returns objects for which the user has the appropriate view permission.

If you're using `DjangoObjectPermissionsFilter`, you'll probably also want to add an appropriate object permissions
class, to ensure that users can only operate on instances if they have the appropriate object permissions.  The easiest
way to do this is to subclass `DjangoObjectPermissions` and add `'view'` permissions to the `perms_map` attribute.

An example using both `DjangoObjectPermissionsFilter` and `DjangoObjectPermissions` might look like the following:

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
    permission_classes = (CustomObjectPermissions,)
    filter_backends = (filters.DjangoObjectPermissionsFilter,)
```

For more information on adding `'view'` permissions for models, see the [relevant section][view-permissions] of the
`django-guardian` documentation, and [this blogpost][view-permissions-blogpost].

[view-permissions]: https://django-guardian.readthedocs.io/en/latest/userguide/assign.html
[view-permissions-blogpost]: https://blog.nyaruka.com/adding-a-view-permission-to-django-models

## Release Process

- Update changelog
- Update package version in setup.py
- Create git tag for version
- Build & upload release to PyPI
  ```bash
  $ pip install -U pip setuptools wheel twine
  $ rm -rf dist/ build/
  $ python setup.py bdist_wheel
  $ twine upload dist/*
  ```
