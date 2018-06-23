import django
from django.db import models
from django.utils.translation import ugettext_lazy as _


class BasicModel(models.Model):
    text = models.CharField(max_length=100, help_text=_('Text description.'))


class BasicPermModel(models.Model):
    text = models.CharField(max_length=100)

    class Meta:
        app_label = 'tests'
        if django.VERSION < (2, 1):
            permissions = (
                # add, change, and delete are builtin permissions
                ('view_basicpermmodel', 'Can view basic perm model'),
            )
