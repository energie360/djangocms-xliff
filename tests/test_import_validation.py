import pytest
from cms.api import create_page
from cms.constants import TEMPLATE_INHERITANCE_MAGIC

from djangocms_xliff.exceptions import XliffImportError
from djangocms_xliff.imports import (
    validate_page_with_xliff_context,
    validate_units_max_lengths,
)
from djangocms_xliff.types import Unit


def test_validate_units_max_length():
    with pytest.raises(XliffImportError):
        validate_units_max_lengths(
            [
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
        )


@pytest.mark.django_db
def test_page_and_context_cant_have_different_id(create_xliff_context):
    page = create_page("Test", TEMPLATE_INHERITANCE_MAGIC, "de")
    xliff_context = create_xliff_context([], page_id=page.id + 1)  # Make sure the ids are always different

    assert page.id != xliff_context.page_id
    with pytest.raises(XliffImportError):
        validate_page_with_xliff_context(page, xliff_context, "de")


@pytest.mark.django_db
def test_current_language_and_context_cant_have_different_target_language(create_xliff_context):
    current_language = "fr"

    page = create_page("Test", TEMPLATE_INHERITANCE_MAGIC, "de")
    xliff_context = create_xliff_context([], target_language="de")

    with pytest.raises(XliffImportError):
        validate_page_with_xliff_context(page, xliff_context, current_language)
