from functools import partial

from cms.api import get_page_draft
from cms.cms_toolbars import LANGUAGE_MENU_IDENTIFIER
from cms.models import Page
from cms.toolbar_base import CMSToolbar
from cms.toolbar_pool import toolbar_pool
from cms.utils import page_permissions
from django.urls import reverse
from django.utils.translation import gettext as _

XLIFF_NAMESPACE = "djangocms_xliff"
XLIFF_LANGUAGE_BREAK = "Export XLIFF Break"


@toolbar_pool.register
class XliffToolbar(CMSToolbar):
    def populate(self):
        super().populate()
        self.draft_page: Page = get_page_draft(self.request.current_page)
        self.update_language_menu()

    def update_language_menu(self):
        if self.toolbar.edit_mode_active and self.draft_page:
            can_change = page_permissions.user_can_change_page(
                user=self.request.user,
                page=self.draft_page,
                site=self.current_site,
            )
        else:
            can_change = False

        if can_change:
            language_menu = self.toolbar.get_menu(LANGUAGE_MENU_IDENTIFIER)
            if not language_menu:
                return None

            if len(self.draft_page.get_languages()) > 1:
                reverse_xliff = partial(
                    reverse,
                    kwargs={
                        "page_id": self.draft_page.pk,
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
