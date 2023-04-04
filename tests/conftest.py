from typing import Tuple

import pytest
from cms.api import add_plugin, create_page
from cms.models import CMSPlugin, Page

from djangocms_xliff.types import XliffContext


@pytest.fixture
def create_xliff_context():
    def _create_xliff_context(units, source_language="de", target_language="fr", page_id=1, page_path="/test"):
        return XliffContext(
            source_language=source_language,
            target_language=target_language,
            page_id=page_id,
            page_path=page_path,
            units=units,
        )

    return _create_xliff_context


@pytest.fixture
def create_draft_page():
    def _create_draft_page(language: str, **extra_kwargs) -> Page:
        page_kwargs = {
            "title": "Test",
            "template": "testing.html",
            "language": language,
            "published": False,
            "slug": "test-example",
            "overwrite_url": "test/example",
        }

        if extra_kwargs:
            page_kwargs.update(**extra_kwargs)

        return create_page(**page_kwargs)

    return _create_draft_page


@pytest.fixture
def page_with_one_field_in_plugin(create_draft_page):
    def _page_with_one_field_in_plugin() -> Tuple[Page, CMSPlugin]:
        language = "en"

        page = create_draft_page(language)
        placeholder = page.placeholders.get(slot="main")

        plugin = add_plugin(placeholder, plugin_type="TestOneFieldPlugin", language=language, body="First plugin")
        return page, plugin

    return _page_with_one_field_in_plugin


@pytest.fixture
def page_with_multiple_fields_in_one_plugin(create_draft_page):
    def _page_with_multiple_fields_in_one_plugin() -> Tuple[Page, CMSPlugin]:
        language = "en"

        page = create_draft_page(language)
        placeholder = page.placeholders.get(slot="main")

        plugin = add_plugin(
            placeholder,
            plugin_type="TestMultipleFieldsPlugin",
            language=language,
            title="Title test",
            lead="Lead test",
            amount=1,
            is_good=False,
        )
        return page, plugin

    return _page_with_multiple_fields_in_one_plugin


@pytest.fixture
def page_with_one_nested_plugin(create_draft_page):
    def _page_with_one_nested_plugin() -> Tuple[Page, CMSPlugin, CMSPlugin]:
        language = "en"

        page = create_draft_page(language)
        placeholder = page.placeholders.get(slot="main")

        parent_plugin = add_plugin(
            placeholder,
            plugin_type="TestParentPlugin",
            language=language,
            body="Parent text",
        )
        child_plugin = add_plugin(
            placeholder, plugin_type="TestChildPlugin", target=parent_plugin, language=language, title="Child text"
        )
        return page, parent_plugin, child_plugin

    return _page_with_one_nested_plugin


@pytest.fixture
def page_with_multiple_placeholders_and_one_plugin(create_draft_page):
    def _page_with_multiple_placeholders_and_one_plugin() -> Tuple[Page, CMSPlugin, CMSPlugin]:
        language = "en"

        page = create_draft_page(language)
        main_placeholder = page.placeholders.get(slot="main")
        second_placeholder = page.placeholders.get(slot="second")

        main_plugin = add_plugin(
            main_placeholder, plugin_type="TestOneFieldPlugin", language=language, body="Plugin in main placeholder"
        )

        second_plugin = add_plugin(
            second_placeholder, plugin_type="TestOneFieldPlugin", language=language, body="Plugin in second placeholder"
        )

        return page, main_plugin, second_plugin

    return _page_with_multiple_placeholders_and_one_plugin


@pytest.fixture
def page_with_multiple_placeholders_and_multiple_plugins(create_draft_page):
    def _page_with_multiple_placeholders_and_multiple_plugins() -> Tuple[Page, CMSPlugin, CMSPlugin, CMSPlugin]:
        language = "en"

        page = create_draft_page(language)
        main_placeholder = page.placeholders.get(slot="main")

        main_plugin_1 = add_plugin(
            main_placeholder,
            plugin_type="TestOneFieldPlugin",
            language=language,
            body="Plugin 1 body in main placeholder",
        )
        main_plugin_2 = add_plugin(
            main_placeholder,
            plugin_type="TestMultipleFieldsPlugin",
            language=language,
            title="Plugin 2 title in main placeholder",
            lead="Plugin 2 lead in main placeholder",
            amount=1,
            is_good=False,
        )

        second_placeholder = page.placeholders.get(slot="second")
        second_plugin = add_plugin(
            second_placeholder,
            plugin_type="TestOneFieldPlugin",
            language=language,
            body="Plugin 1 body in second placeholder",
        )

        return page, main_plugin_1, main_plugin_2, second_plugin

    return _page_with_multiple_placeholders_and_multiple_plugins


@pytest.fixture
def page_with_metadata(create_draft_page):
    return create_draft_page(
        language="en",
        title="Title Test",
        menu_title="Menu Title Test",
        page_title="Page Title Test",
        meta_description="Menu Description Test",
    )
