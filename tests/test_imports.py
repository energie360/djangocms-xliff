from typing import List

import pytest
from cms.api import create_page
from cms.models import CMSPlugin

from djangocms_xliff.exceptions import XliffImportError
from djangocms_xliff.extractors import extract_units_from_obj
from djangocms_xliff.imports import (
    save_xliff_context,
    validate_page_with_xliff_context,
    validate_units_max_lengths,
)
from djangocms_xliff.types import Unit


def get_character_length_test_units() -> List[Unit]:
    return [
        Unit(
            plugin_id=123,
            plugin_type="TestPlugin",
            plugin_name="Test plugin",
            field_name="title",
            field_type="django.db.models.CharField",
            source="Willkommen",
            target="Welcome",
            max_length=30,
        ),
        Unit(
            plugin_id=123,
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
def test_page_and_context_cant_have_different_id(create_xliff_page_context):
    page = create_page("Test", "testing.html", "de")
    xliff_context = create_xliff_page_context([], obj_id=page.id + 1)  # Make sure the ids are always different

    assert page.id != xliff_context.obj_id
    with pytest.raises(XliffImportError):
        validate_page_with_xliff_context(page, xliff_context, "de")


@pytest.mark.django_db
def test_current_language_and_context_cant_have_different_target_language(create_xliff_page_context):
    current_language = "fr"

    page = create_page("Test", "testing.html", "de")
    xliff_context = create_xliff_page_context([], target_language="de")

    with pytest.raises(XliffImportError):
        validate_page_with_xliff_context(page, xliff_context, current_language)


@pytest.mark.django_db
def test_extract_and_save_xliff_context(create_xliff_page_context, page_with_multiple_placeholders_and_multiple_plugins):
    """
    This is an integration test, to see if extraction and import work
    It's basically what's happening in the UI, without validation
    """
    language_to_translate = "en"

    # Create page, placeholder and plugins
    page, main_plugin_1, main_plugin_2, second_plugin = page_with_multiple_placeholders_and_multiple_plugins()

    # Extract the xliff units from the page
    units = extract_units_from_obj(page, language_to_translate)
    xliff_context = create_xliff_page_context(
        units,
        source_language="de",
        target_language=language_to_translate,
        obj_id=page.pk,
        path=page.get_path(language_to_translate),
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
