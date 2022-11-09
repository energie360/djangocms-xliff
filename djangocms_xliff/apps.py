from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class DjangoCMSXliffConfig(AppConfig):
    name = "djangocms_xliff"
    verbose_name = _("Django CMS XLIFF Import / Export")
