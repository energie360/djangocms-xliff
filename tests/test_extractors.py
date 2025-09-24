from functools import partial
from typing import List

import pytest
from cms.models import PageContent

from djangocms_xliff.extractors import (
    extract_extension_data_from_page,
    extract_metadata_from_obj,
    extract_units_from_obj,
    extract_units_from_placeholder,
    extract_units_from_plugin,
    extract_units_from_plugin_instance,
)
from djangocms_xliff.settings import PAGE_CONTENT_METADATA_FIELDS, UNIT_ID_METADATA_ID
from djangocms_xliff.types import Unit
from djangocms_xliff.utils import get_plugin_id_for_extension_obj, get_type_with_path
from tests.conftest import get_page_placeholder


def page_with_one_field_expected_units() -> List[Unit]:
    return [
        Unit(
            plugin_id="1",
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

    placeholder = get_page_placeholder(page=page, slot="main", language="en")

    assert extract_units_from_placeholder(placeholder, "en") == page_with_one_field_expected_units()


@pytest.mark.django_db
def test_extract_units_from_page_one_field(page_with_one_field_in_plugin):
    page, _ = page_with_one_field_in_plugin()
    obj = PageContent.admin_manager.get(page=page, language="en")

    assert extract_units_from_obj(obj, "en", include_metadata=False) == page_with_one_field_expected_units()


@pytest.mark.django_db
def test_extract_units_from_page_multiple_fields(page_with_multiple_fields_in_one_plugin):
    page, plugin = page_with_multiple_fields_in_one_plugin()

    expected = [
        Unit(
            plugin_id=str(plugin.pk),
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
            plugin_id=str(plugin.pk),
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

    obj = PageContent.admin_manager.get(page=page, language="en")

    assert extract_units_from_obj(obj, "en", include_metadata=False) == expected


@pytest.mark.django_db
def test_extract_units_from_page_nested_plugin(page_with_one_nested_plugin):
    page, parent_plugin, child_plugin = page_with_one_nested_plugin()

    expected = [
        Unit(
            plugin_id=str(parent_plugin.pk),
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
            plugin_id=str(child_plugin.pk),
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

    obj = PageContent.admin_manager.get(page=page, language="en")

    assert extract_units_from_obj(obj, "en", include_metadata=False) == expected


@pytest.mark.django_db
def test_extract_units_form_page_multiple_placeholders_one_plugin(page_with_multiple_placeholders_and_one_plugin):
    page, main_plugin, second_plugin = page_with_multiple_placeholders_and_one_plugin()

    expected = [
        Unit(
            plugin_id=str(main_plugin.pk),
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
            plugin_id=str(second_plugin.pk),
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

    obj = PageContent.admin_manager.get(page=page, language="en")

    assert extract_units_from_obj(obj, "en", include_metadata=False) == expected


@pytest.mark.django_db
def test_extract_units_form_page_multiple_placeholders_multiple_plugins(
    page_with_multiple_placeholders_and_multiple_plugins,
):
    page, main_plugin_1, main_plugin_2, second_plugin = page_with_multiple_placeholders_and_multiple_plugins()

    expected = [
        Unit(
            plugin_id=str(main_plugin_1.pk),
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
            plugin_id=str(main_plugin_2.pk),
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
            plugin_id=str(main_plugin_2.pk),
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
            plugin_id=str(second_plugin.pk),
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

    obj = PageContent.admin_manager.get(page=page, language="en")

    assert extract_units_from_obj(obj, "en", include_metadata=False) == expected


@pytest.mark.django_db
def test_extract_units_from_model(model_with_static_placeholder):
    test_model, _ = model_with_static_placeholder()

    assert extract_units_from_obj(test_model, "en", include_metadata=False) == page_with_one_field_expected_units()


@pytest.mark.django_db
def test_extract_metadata_units_form_page(page_with_metadata):
    language = "en"

    page_unit = partial(
        Unit,
        plugin_id=UNIT_ID_METADATA_ID,
        plugin_type=UNIT_ID_METADATA_ID,
        plugin_name=UNIT_ID_METADATA_ID,
    )
    title_obj = page_with_metadata.get_content_obj(language=language)

    computed = extract_metadata_from_obj(
        obj=page_with_metadata,
        language=language,
        plugin_name=UNIT_ID_METADATA_ID,
        plugin_type=UNIT_ID_METADATA_ID,
        plugin_id=UNIT_ID_METADATA_ID,
    )

    expected = []
    fields = PAGE_CONTENT_METADATA_FIELDS
    for field_name, field_verbose_name in fields.items():
        field = title_obj._meta.get_field(field_name)
        expected.append(
            page_unit(
                field_name=field_name,
                source=field.value_from_object(title_obj),
                target="",
                field_verbose_name=field_verbose_name,
                max_length=field.max_length,
                field_type=get_type_with_path(field),
            )
        )
    assert computed == expected


@pytest.mark.django_db
def test_extract_metadata_units_from_model(monkeypatch, model_with_metadata):
    model_unit = partial(
        Unit,
        plugin_id=UNIT_ID_METADATA_ID,
        plugin_type=UNIT_ID_METADATA_ID,
        plugin_name=UNIT_ID_METADATA_ID,
    )

    computed = extract_metadata_from_obj(
        obj=model_with_metadata,
        language="en",
        plugin_name=UNIT_ID_METADATA_ID,
        plugin_type=UNIT_ID_METADATA_ID,
        plugin_id=UNIT_ID_METADATA_ID,
    )

    expected = []
    for field in model_with_metadata._meta.fields:
        if field.name in ["id"]:
            continue

        expected.append(
            model_unit(
                field_name=field.name,
                source=field.value_from_object(model_with_metadata),
                target="",
                field_verbose_name=field.verbose_name,
                max_length=field.max_length,
                field_type=get_type_with_path(field),
            )
        )

    assert computed == expected


@pytest.mark.django_db
def test_extract_units_from_page_extension(page_with_page_extension):
    computed = extract_extension_data_from_page(obj=page_with_page_extension, language="en")

    model_unit = partial(
        Unit,
        plugin_id=get_plugin_id_for_extension_obj(page_with_page_extension.testpageextension),
        plugin_type=page_with_page_extension.testpageextension._meta.object_name,
        plugin_name=page_with_page_extension.testpageextension._meta.verbose_name,
    )

    expected = []
    for field in page_with_page_extension.testpageextension._meta.fields:
        if field.name in ["id", "public_extension", "extended_object"]:
            continue

        expected.append(
            model_unit(
                field_name=field.name,
                source=page_with_page_extension.testpageextension.title,
                target="",
                field_verbose_name=field.verbose_name,
                max_length=field.max_length,
                field_type=get_type_with_path(field),
            )
        )

    assert computed == expected


@pytest.mark.django_db
def test_extract_units_from_title_extension(page_with_title_extension):
    computed = extract_extension_data_from_page(obj=page_with_title_extension, language="en")

    title = page_with_title_extension.get_content_obj(language="en")

    model_unit = partial(
        Unit,
        plugin_id=get_plugin_id_for_extension_obj(title.testtitleextension),
        plugin_type=title.testtitleextension._meta.object_name,
        plugin_name=title.testtitleextension._meta.verbose_name,
    )

    expected = []
    for field in title.testtitleextension._meta.fields:
        if field.name in ["id", "public_extension", "extended_object"]:
            continue

        expected.append(
            model_unit(
                field_name=field.name,
                source=title.testtitleextension.title,
                target="",
                field_verbose_name=field.verbose_name,
                max_length=field.max_length,
                field_type=get_type_with_path(field),
            )
        )

    assert computed == expected
