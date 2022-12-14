#  type: ignore
from cms.models import CMSPlugin
from django.db import models


class TestOneFieldModel(CMSPlugin):
    body = models.CharField(max_length=100, verbose_name="Body")

    class Meta:
        verbose_name = "Test one field model"


class TestMultipleFieldsModel(CMSPlugin):
    title = models.CharField(max_length=100, verbose_name="Title")
    lead = models.TextField(verbose_name="Lead")
    amount = models.IntegerField(verbose_name="Anzahl")
    is_good = models.BooleanField(verbose_name="All good")

    class Meta:
        verbose_name = "Test multiple fields model "


class TestParentModel(CMSPlugin):
    body = models.CharField(max_length=100, verbose_name="Body")

    class Meta:
        verbose_name = "Test Parent Model"


class TestChildModel(CMSPlugin):
    title = models.CharField(max_length=200, verbose_name="Title")

    class Meta:
        verbose_name = "Test Child Model"
