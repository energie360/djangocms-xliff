from typing import List

import pytest

from djangocms_xliff.extractors import (
    extract_units_from_obj,
    extract_units_from_placeholder,
    extract_units_from_plugin,
    extract_units_from_plugin_instance,
)
from djangocms_xliff.types import Unit


def page_with_one_field_expected_units() -> List[Unit]:
    return [
        Unit(
            plugin_id=1,
            plugin_type="TestOneFieldPlugin",
            plugin_name="Test one field plugin",
            field_name="body",
            field_type="django.db.models.fields.CharField",
            source="First plugin",
            target="",
            field_verbose_name="Body",
            max_length=100,
        )
    ]


@pytest.mark.django_db
def test_extract_units_from_plugin_instance(page_with_one_field_in_plugin):
    page, test_plugin = page_with_one_field_in_plugin()

    instance, plugin = test_plugin.get_plugin_instance()

    assert extract_units_from_plugin_instance(instance) == page_with_one_field_expected_units()


@pytest.mark.django_db
def test_extract_units_from_plugin(page_with_one_field_in_plugin):
    page, test_plugin = page_with_one_field_in_plugin()

    assert extract_units_from_plugin(test_plugin) == page_with_one_field_expected_units()


@pytest.mark.django_db
def test_extract_units_from_placeholder(page_with_one_field_in_plugin):
    page, test_plugin = page_with_one_field_in_plugin()

    placeholder = page.placeholders.get(slot="main")

    assert extract_units_from_placeholder(placeholder, "en") == page_with_one_field_expected_units()


@pytest.mark.django_db
def test_extract_units_from_page_one_field(page_with_one_field_in_plugin):
    page, _ = page_with_one_field_in_plugin()

    assert extract_units_from_obj(page, "en") == page_with_one_field_expected_units()


@pytest.mark.django_db
def test_extract_units_from_page_multiple_fields(page_with_multiple_fields_in_one_plugin):
    page, plugin = page_with_multiple_fields_in_one_plugin()

    expected = [
        Unit(
            plugin_id=plugin.pk,
            plugin_type="TestMultipleFieldsPlugin",
            plugin_name="Test multiple fields plugin",
            field_name="title",
            field_type="django.db.models.fields.CharField",
            source="Title test",
            target="",
            field_verbose_name="Title",
            max_length=100,
        ),
        Unit(
            plugin_id=plugin.pk,
            plugin_type="TestMultipleFieldsPlugin",
            plugin_name="Test multiple fields plugin",
            field_name="lead",
            field_type="django.db.models.fields.TextField",
            source="Lead test",
            target="",
            field_verbose_name="Lead",
            max_length=None,
        ),
    ]

    assert extract_units_from_obj(page, "en") == expected


@pytest.mark.django_db
def test_extract_units_from_page_nested_plugin(page_with_one_nested_plugin):
    page, parent_plugin, child_plugin = page_with_one_nested_plugin()

    expected = [
        Unit(
            plugin_id=parent_plugin.pk,
            plugin_type="TestParentPlugin",
            plugin_name="Test parent plugin",
            field_name="body",
            field_type="django.db.models.fields.CharField",
            source="Parent text",
            target="",
            field_verbose_name="Body",
            max_length=100,
        ),
        Unit(
            plugin_id=child_plugin.pk,
            plugin_type="TestChildPlugin",
            plugin_name="Test child plugin",
            field_name="title",
            field_type="django.db.models.fields.CharField",
            source="Child text",
            target="",
            field_verbose_name="Title",
            max_length=200,
        ),
    ]

    assert extract_units_from_obj(page, "en") == expected


@pytest.mark.django_db
def test_extract_units_form_page_multiple_placeholders_one_plugin(page_with_multiple_placeholders_and_one_plugin):
    page, main_plugin, second_plugin = page_with_multiple_placeholders_and_one_plugin()

    expected = [
        Unit(
            plugin_id=main_plugin.pk,
            plugin_type="TestOneFieldPlugin",
            plugin_name="Test one field plugin",
            field_name="body",
            field_type="django.db.models.fields.CharField",
            source="Plugin in main placeholder",
            target="",
            field_verbose_name="Body",
            max_length=100,
        ),
        Unit(
            plugin_id=second_plugin.pk,
            plugin_type="TestOneFieldPlugin",
            plugin_name="Test one field plugin",
            field_name="body",
            field_type="django.db.models.fields.CharField",
            source="Plugin in second placeholder",
            target="",
            field_verbose_name="Body",
            max_length=100,
        ),
    ]

    assert extract_units_from_obj(page, "en") == expected


@pytest.mark.django_db
def test_extract_units_form_page_multiple_placeholders_multiple_plugins(
        page_with_multiple_placeholders_and_multiple_plugins,
):
    page, main_plugin_1, main_plugin_2, second_plugin = page_with_multiple_placeholders_and_multiple_plugins()

    expected = [
        Unit(
            plugin_id=main_plugin_1.pk,
            plugin_type="TestOneFieldPlugin",
            plugin_name="Test one field plugin",
            field_name="body",
            field_type="django.db.models.fields.CharField",
            source="Plugin 1 body in main placeholder",
            target="",
            field_verbose_name="Body",
            max_length=100,
        ),
        Unit(
            plugin_id=main_plugin_2.pk,
            plugin_type="TestMultipleFieldsPlugin",
            plugin_name="Test multiple fields plugin",
            field_name="title",
            field_type="django.db.models.fields.CharField",
            source="Plugin 2 title in main placeholder",
            target="",
            field_verbose_name="Title",
            max_length=100,
        ),
        Unit(
            plugin_id=main_plugin_2.pk,
            plugin_type="TestMultipleFieldsPlugin",
            plugin_name="Test multiple fields plugin",
            field_name="lead",
            field_type="django.db.models.fields.TextField",
            source="Plugin 2 lead in main placeholder",
            target="",
            field_verbose_name="Lead",
            max_length=None,
        ),
        Unit(
            plugin_id=second_plugin.pk,
            plugin_type="TestOneFieldPlugin",
            plugin_name="Test one field plugin",
            field_name="body",
            field_type="django.db.models.fields.CharField",
            source="Plugin 1 body in second placeholder",
            target="",
            field_verbose_name="Body",
            max_length=100,
        ),
    ]

    assert extract_units_from_obj(page, "en") == expected
