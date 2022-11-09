from django.template.exceptions import TemplateDoesNotExist
from django.template.loader import render_to_string

from djangocms_xliff.apps import DjangoCMSXliffConfig
from djangocms_xliff.exceptions import XliffConfigurationError
from djangocms_xliff.settings import XliffVersion
from djangocms_xliff.types import XliffContext
from djangocms_xliff.utils import (
    get_xliff_export_template_name,
    get_xliff_xml_namespaces,
)


def render_xliff_document(version: XliffVersion, context: XliffContext) -> str:
    template_name = get_xliff_export_template_name(version)
    xml_namespaces = get_xliff_xml_namespaces(version)
    try:
        return render_to_string(
            template_name=template_name,
            context={
                "version": version.value,
                "xml_namespaces": xml_namespaces,
                "tool": {
                    "name": DjangoCMSXliffConfig.name,
                    "company": "Energie 360°",
                },
                "xliff": context,
            },
        )
    except TemplateDoesNotExist:
        raise XliffConfigurationError(f"Template does not exist: {template_name}")
