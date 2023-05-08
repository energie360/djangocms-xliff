from functools import partial

from cms.cms_toolbars import LANGUAGE_MENU_IDENTIFIER
from cms.models import Page
from cms.toolbar_base import CMSToolbar
from cms.toolbar_pool import toolbar_pool
from cms.utils import page_permissions
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from django.utils.translation import gettext as _

XLIFF_NAMESPACE = "djangocms_xliff"
XLIFF_LANGUAGE_BREAK = "Export XLIFF Break"


class XliffToolbar(CMSToolbar):
    def populate(self):
        super().populate()
        obj = self.get_object()
        if obj and self.user_has_permissions(obj=obj):
            self.update_language_menu(obj=obj)

    def get_object(self):
        return self.toolbar.obj or self.request.current_page

    def user_has_permissions(self, obj) -> bool:
        return False

    def update_language_menu(self, obj):
        language_menu = self.toolbar.get_menu(LANGUAGE_MENU_IDENTIFIER)
        if not language_menu:
            return None

        content_type_id = ContentType.objects.get_for_model(obj.__class__).id
        reverse_xliff = partial(
            reverse,
            kwargs={
                "content_type_id": content_type_id,
                "obj_id": obj.id,
                "current_language": self.current_lang,
            },
        )

        language_menu.add_break(XLIFF_LANGUAGE_BREAK)
        language_menu.add_modal_item(
            _("Export as XLIFF"),
            reverse_xliff(viewname="djangocms_xliff:export"),
        )
        language_menu.add_modal_item(
            _("Import from XLIFF"),
            reverse_xliff(viewname="djangocms_xliff:upload"),
        )


@toolbar_pool.register
class XliffPageToolbar(XliffToolbar):
    def user_has_permissions(self, obj) -> bool:
        if hasattr(obj, "_wrapped"):  # request.current_page returns a SimpleLazyObject
            obj = obj._wrapped

        if self.toolbar.edit_mode_active and obj and type(obj) == Page and len(obj.get_languages()) > 1:
            return page_permissions.user_can_change_page(user=self.request.user, page=obj, site=self.current_site)
        return False


class XliffModelToolbar(XliffToolbar):
    """
    Inherit from this class to add xliff import and export functionality to your custom models
    """

    def user_has_permissions(self, obj) -> bool:
        if self.toolbar.edit_mode_active and obj and type(obj) != Page:
            return self.request.user.has_perm(f"{obj._meta.app_label}.change_{obj._meta.model_name}")
        return False
