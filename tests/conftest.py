from typing import Tuple

import pytest
from cms.api import add_plugin, create_page
from cms.models import CMSPlugin, Page, StaticPlaceholder
from django.contrib.contenttypes.models import ContentType
from django.db.models import Model

from djangocms_xliff.types import XliffContext
from tests.models import (
    TestModelMetadata,
    TestModelStaticPlaceholder,
    TestPageExtension,
    TestTitleExtension,
)


def get_page_placeholder(page: Page, slot: str, language: str):
    return page.get_placeholders(language).get(slot=slot)


@pytest.fixture
def create_xliff_page_context():
    def _create_xliff_page_context(units, source_language="de", target_language="fr", obj_id=1, path="/test"):
        return XliffContext(
            source_language=source_language,
            target_language=target_language,
            content_type_id=ContentType.objects.get_for_model(Page).pk,
            obj_id=obj_id,
            path=path,
            units=units,
        )

    return _create_xliff_page_context


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
        placeholder = get_page_placeholder(page=page, slot="main", language=language)

        plugin = add_plugin(placeholder, plugin_type="TestOneFieldPlugin", language=language, body="First plugin")
        return page, plugin

    return _page_with_one_field_in_plugin


@pytest.fixture
def page_with_multiple_fields_in_one_plugin(create_draft_page):
    def _page_with_multiple_fields_in_one_plugin() -> Tuple[Page, CMSPlugin]:
        language = "en"

        page = create_draft_page(language)
        placeholder = get_page_placeholder(page=page, slot="main", language=language)

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
        placeholder = get_page_placeholder(page=page, slot="main", language=language)

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
        main_placeholder = get_page_placeholder(page=page, slot="main", language=language)
        second_placeholder = get_page_placeholder(page=page, slot="second", language=language)

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
        main_placeholder = get_page_placeholder(page=page, slot="main", language=language)

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

        second_placeholder = get_page_placeholder(page=page, slot="second", language=language)
        second_plugin = add_plugin(
            second_placeholder,
            plugin_type="TestOneFieldPlugin",
            language=language,
            body="Plugin 1 body in second placeholder",
        )

        return page, main_plugin_1, main_plugin_2, second_plugin

    return _page_with_multiple_placeholders_and_multiple_plugins


@pytest.fixture
def model_with_static_placeholder():
    def _model_with_one_field_in_plugin() -> Tuple[Model, CMSPlugin]:
        language = "en"

        static_placeholder = StaticPlaceholder.objects.create(name="test", code="main")

        plugin = add_plugin(
            static_placeholder.draft, plugin_type="TestOneFieldPlugin", language=language, body="First plugin"
        )

        test_model = TestModelStaticPlaceholder.objects.create(placeholder=static_placeholder)

        return test_model, plugin

    return _model_with_one_field_in_plugin


@pytest.fixture
def page_with_metadata(create_draft_page) -> Page:
    page_kwargs = {
        "language": "en",
        "title": "Title Test",
        "menu_title": "Menu Title Test",
        "meta_description": "Meta Description Test",
    }
    return create_draft_page(**page_kwargs)


@pytest.fixture
def page_with_page_extension(create_draft_page) -> Page:
    language = "en"

    page = create_draft_page(language)
    TestPageExtension.objects.create(title="Title Test", extended_object=page)
    return page


@pytest.fixture
def page_with_title_extension(create_draft_page) -> Page:
    language = "en"

    page = create_draft_page(language)
    extended_object = page.get_content_obj(language)
    TestTitleExtension.objects.create(title="Title Test", extended_object=extended_object)
    return page


@pytest.fixture
def model_with_metadata() -> TestModelMetadata:
    return TestModelMetadata.objects.create(
        title="Title Test",
        slug="model-slug",
        meta_description="Meta Description for Model",
    )
