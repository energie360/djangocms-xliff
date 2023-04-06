from enum import Enum, unique

from django.conf import settings
from django.utils.module_loading import import_string


@unique
class XliffVersion(Enum):
    V1_2 = "1.2"


XLIFF_NAMESPACES = {XliffVersion.V1_2: {"": "urn:oasis:names:tc:xliff:document:1.2"}}

UNIT_ID_DELIMITER = "__"
UNIT_ID_METADATA_ID = "METADATA"

TEMPLATES_FOLDER = "djangocms_xliff"
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
