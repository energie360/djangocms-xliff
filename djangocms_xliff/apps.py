from django.apps import AppConfig
from django.utils.translation import gettext_lazy


class DjangoCMSXliffConfig(AppConfig):
    name = "djangocms_xliff"
    verbose_name = gettext_lazy("Django CMS XLIFF Import / Export")
