from functools import partial
from typing import List

import pytest
from cms.api import create_page
from cms.models import CMSPlugin, Page

from djangocms_xliff.exceptions import XliffImportError
from djangocms_xliff.extractors import extract_units_from_page
from djangocms_xliff.imports import (
    save_xliff_context,
    validate_page_with_xliff_context,
    validate_units_max_lengths,
)
from djangocms_xliff.settings import UNIT_ID_METADATA_ID
from djangocms_xliff.types import Unit


def get_character_length_test_units() -> List[Unit]:
    return [
        Unit(
            plugin_id="123",
            plugin_type="TestPlugin",
            plugin_name="Test plugin",
            field_name="title",
            field_type="django.db.models.CharField",
            source="Willkommen",
            target="Welcome",
            max_length=30,
        ),
        Unit(
            plugin_id="123",
            plugin_type="TestPlugin",
            plugin_name="Test plugin",
            field_name="lead",
            field_type="django.db.models.CharField",
            source="Das ist ein langer text",
            target="This is a reaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaly long text",
            max_length=30,
        ),
    ]


def test_unit_max_length_exceeded():
    checks = [u.is_max_length_exceeded() for u in get_character_length_test_units()]

    assert checks == [False, True]


def test_validate_units_max_length():
    with pytest.raises(XliffImportError):
        validate_units_max_lengths(get_character_length_test_units())


@pytest.mark.django_db
def test_page_and_context_cant_have_different_id(create_xliff_context):
    page = create_page("Test", "testing.html", "de")
    xliff_context = create_xliff_context([], page_id=page.pk + 1)  # Make sure the ids are always different

    assert page.pk != xliff_context.page_id
    with pytest.raises(XliffImportError):
        validate_page_with_xliff_context(page, xliff_context, "de")


@pytest.mark.django_db
def test_current_language_and_context_cant_have_different_target_language(create_xliff_context):
    current_language = "fr"

    page = create_page("Test", "testing.html", "de")
    xliff_context = create_xliff_context([], target_language="de")

    with pytest.raises(XliffImportError):
        validate_page_with_xliff_context(page, xliff_context, current_language)


@pytest.mark.django_db
def test_extract_and_save_xliff_context(create_xliff_context, page_with_multiple_placeholders_and_multiple_plugins):
    """
    This is an integration test, to see if extraction and import work
    It's basically what's happening in the UI, without validation
    """
    language_to_translate = "en"

    # Create page, placeholder and plugins
    page, main_plugin_1, main_plugin_2, second_plugin = page_with_multiple_placeholders_and_multiple_plugins()

    # Extract the xliff units from the page
    units = extract_units_from_page(page, language_to_translate, include_metadata=False)
    xliff_context = create_xliff_context(
        units,
        source_language="de",
        target_language=language_to_translate,
        page_id=page.pk,
        page_path=page.get_path(language_to_translate),
    )

    # Translate units
    main_plugin_1_target_text = "Plugin 1 body wurde übersetzt"
    xliff_context.units[0].target = main_plugin_1_target_text

    main_plugin_2_target_text_title = "Plugin 2 title wurde übersetzt"
    xliff_context.units[1].target = main_plugin_2_target_text_title

    main_plugin_2_target_text_lead = "Plugin 2 lead wurde übersetzt"
    xliff_context.units[2].target = main_plugin_2_target_text_lead

    # Import the units
    save_xliff_context(xliff_context)

    # Reload the plugins from the database
    main_plugin_1_updated = CMSPlugin.objects.get(pk=main_plugin_1.pk).get_bound_plugin()
    main_plugin_2_updated = CMSPlugin.objects.get(pk=main_plugin_2.pk).get_bound_plugin()

    # Check if the plugins were updated
    assert main_plugin_1_updated.body == main_plugin_1_target_text
    assert main_plugin_2_updated.title == main_plugin_2_target_text_title
    assert main_plugin_2_updated.lead == main_plugin_2_target_text_lead


@pytest.mark.django_db
def test_save_page_with_metadata(page_with_metadata, create_xliff_context):
    language_to_translate = "de"

    # Translate units
    title_target_text = "Titel übersetzt"
    slug_target_text = "Slug übersetzt"
    page_title_target_text = "Seitentitel übersetzt"
    menu_title_target_text = "Menütitel übersetzt"
    meta_description_target_text = "Meta Beschreibung übersetzt"

    page_unit = partial(
        Unit,
        plugin_id=UNIT_ID_METADATA_ID,
        plugin_type=UNIT_ID_METADATA_ID,
        plugin_name=UNIT_ID_METADATA_ID,
        field_type="django.db.models.fields.CharField",
    )

    title_obj = page_with_metadata.get_title_obj(language="en")

    units = [
        page_unit(
            field_name="title",
            source=title_obj.title,
            target=title_target_text,
            field_verbose_name="Title",
            max_length=255,
        ),
        page_unit(
            field_name="page_title",
            source=title_obj.page_title,
            target=page_title_target_text,
            field_verbose_name="Page Title",
            max_length=255,
        ),
        page_unit(
            field_name="slug",
            source=title_obj.page_title,
            target=slug_target_text,
            field_verbose_name="Slug",
            max_length=255,
        ),
        page_unit(
            field_name="menu_title",
            source=title_obj.menu_title,
            target=menu_title_target_text,
            field_verbose_name="Menu Title",
            max_length=255,
        ),
        page_unit(
            field_type="django.db.models.fields.TextField",
            field_name="meta_description",
            source=title_obj.meta_description,
            target=meta_description_target_text,
            field_verbose_name="Description meta tag",
            max_length=None,
        ),
    ]

    xliff_context = create_xliff_context(
        units,
        source_language="en",
        target_language=language_to_translate,
        page_id=page_with_metadata.pk,
        page_path=page_with_metadata.get_path(language_to_translate),
    )

    # Import the units
    save_xliff_context(xliff_context)

    updated_page = Page.objects.get(pk=xliff_context.page_id)
    updated_title_obj = updated_page.get_title_obj(language=language_to_translate)

    assert updated_title_obj.title == title_target_text
    assert updated_title_obj.menu_title == menu_title_target_text
    assert updated_title_obj.page_title == page_title_target_text
    assert updated_title_obj.meta_description == meta_description_target_text
