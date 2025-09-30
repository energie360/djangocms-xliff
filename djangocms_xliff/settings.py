from enum import Enum, unique

from django.conf import settings
from django.utils.module_loading import import_string
from django.utils.translation import gettext_lazy


@unique
class XliffVersion(Enum):
    V1_2 = "1.2"


XLIFF_NAMESPACES = {XliffVersion.V1_2: {"": "urn:oasis:names:tc:xliff:document:1.2"}}

UNIT_ID_DELIMITER = "__"
UNIT_ID_METADATA_ID = "METADATA"
UNIT_ID_EXTENSION_DATA_ID = "EXTENSION"

TEMPLATES_FOLDER = "djangocms_xliff"
TEMPLATES_FOLDER_ADMIN = f"{TEMPLATES_FOLDER}/admin/xliff"
TEMPLATES_FOLDER_EXPORT = f"{TEMPLATES_FOLDER}/export"
TEMPLATES_FOLDER_IMPORT = f"{TEMPLATES_FOLDER}/import"

FIELDS = [import_string(field_class) for field_class in getattr(settings, "DJANGOCMS_XLIFF_FIELDS", ())]

FIELD_EXTRACTORS = {
    import_string(field_class): import_string(extractor_callable)
    for field_class, extractor_callable in getattr(settings, "DJANGOCMS_XLIFF_FIELD_EXTRACTORS", ())
}

FIELD_IMPORTERS = {
    field_class: import_string(extractor_callable)
    for field_class, extractor_callable in getattr(settings, "DJANGOCMS_XLIFF_FIELD_IMPORTERS", ())
}

VALIDATORS = [
    import_string(validator_callable) for validator_callable in getattr(settings, "DJANGOCMS_XLIFF_VALIDATORS", ())
]

METADATA_FIELDS = {
    "title": gettext_lazy("Title"),
    "page_title": gettext_lazy("Page Title"),
    "meta_description": gettext_lazy("Description meta tag"),
    "menu_title": gettext_lazy("Menu Title"),
    "slug": gettext_lazy("Slug"),
}

PAGE_URL_FIELDS = {"slug"}

MODEL_METADATA_FIELDS = {
    import_string(model_class): config
    for model_class, config in getattr(settings, "DJANGOCMS_XLIFF_MODEL_METADATA_FIELDS", {}).items()
}

MODEL_FOR_ALIAS_CONTENT = getattr(settings, "DJANGOCMS_XLIFF_MODEL_FOR_ALIAS_CONTENT", "")
get_model_for_alias_content = import_string(MODEL_FOR_ALIAS_CONTENT) if MODEL_FOR_ALIAS_CONTENT else None
