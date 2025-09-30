from functools import partial

from cms.cms_toolbars import LANGUAGE_MENU_IDENTIFIER
from cms.models import PageContent
from cms.toolbar_base import CMSToolbar
from cms.toolbar_pool import toolbar_pool
from cms.utils.page_permissions import user_can_change_page
from cms.utils.permissions import get_model_permission_codename
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from django.utils.translation import gettext
from djangocms_alias.models import AliasContent

XLIFF_NAMESPACE = "djangocms_xliff"
XLIFF_LANGUAGE_BREAK = "Export XLIFF Break"


class XliffToolbar(CMSToolbar):
    def post_template_populate(self):
        super().post_template_populate()
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

        content_type_id = ContentType.objects.get_for_model(obj.__class__).pk
        reverse_xliff = partial(
            reverse,
            kwargs={
                "content_type_id": content_type_id,
                "obj_id": obj.pk,
                "current_language": self.current_lang,
            },
        )

        language_menu.add_break(XLIFF_LANGUAGE_BREAK)
        language_menu.add_modal_item(
            gettext("Export as XLIFF"),
            reverse_xliff(viewname="djangocms_xliff:export"),
        )
        language_menu.add_modal_item(
            gettext("Import from XLIFF"),
            reverse_xliff(viewname="djangocms_xliff:upload"),
        )

    def is_page_content(self, obj) -> bool:
        return type(obj) is PageContent

    def is_alias_content(self, obj) -> bool:
        return type(obj) is AliasContent


@toolbar_pool.register
class XliffPageContentToolbar(XliffToolbar):
    def user_has_permissions(self, obj) -> bool:
        if not self.toolbar.edit_mode_active or not obj or not self.is_page_content(obj):
            return False

        if len(obj.page.get_languages()) <= 1:
            return False

        return user_can_change_page(user=self.request.user, page=obj.page, site=self.current_site)


@toolbar_pool.register
class XliffAliasContentToolbar(XliffToolbar):
    def user_has_permissions(self, obj) -> bool:
        if not self.toolbar.edit_mode_active or not obj or not self.is_alias_content(obj):
            return False

        if len(obj.alias.get_languages()) <= 1:
            return False

        return self.request.user.has_perm(get_model_permission_codename(AliasContent, "change"))


class XliffModelToolbar(XliffToolbar):
    """
    Inherit from this class to add xliff import and export functionality to your custom models
    """

    def user_has_permissions(self, obj) -> bool:
        if not self.toolbar.edit_mode_active or not obj:
            return False

        return self.request.user.has_perm(f"{obj._meta.app_label}.change_{obj._meta.model_name}")
