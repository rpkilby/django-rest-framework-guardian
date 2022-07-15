from django.db import models
from django.utils.translation import gettext_lazy as _


class BasicModel(models.Model):
    text = models.CharField(max_length=100, help_text=_('Text description.'))


class BasicPermModel(models.Model):
    text = models.CharField(max_length=100)

    class Meta:
        app_label = 'tests'
