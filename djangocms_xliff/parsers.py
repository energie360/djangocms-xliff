from html import unescape
from xml.etree.ElementTree import Element, ParseError

from defusedxml.ElementTree import parse
from django.utils.translation import gettext as _

from djangocms_xliff.exceptions import XliffConfigurationError, XliffError
from djangocms_xliff.settings import UNIT_ID_DELIMITER, XliffVersion
from djangocms_xliff.types import Unit, XliffContext
from djangocms_xliff.utils import get_xliff_namespaces, get_xliff_version


def _parse_xliff_units_version_1_2(xml_namespaces: dict, body_element: Element):
    units = []
    for trans_unit in body_element.findall("trans-unit", namespaces=xml_namespaces):
        unit_id = trans_unit.attrib["id"]
        plugin_id, field_name = unit_id.split(UNIT_ID_DELIMITER, 1)

        field_type = trans_unit.attrib["extype"]

        max_length = trans_unit.attrib.get("maxwidth")

        source_element = trans_unit.find("source", namespaces=xml_namespaces)
        if source_element is None:
            raise XliffError("XLIFF Error: Missing <source> in <trans-unit>")

        target_element = trans_unit.find("target", namespaces=xml_namespaces)
        if target_element is None:
            raise XliffError("XLIFF Error: Missing <target> in <trans-unit>")

        source = unescape(source_element.text if source_element.text else "")
        target = unescape(target_element.text if target_element.text else source)

        notes = trans_unit.iterfind("note", namespaces=xml_namespaces)
        plugin_type = next(notes).text
        plugin_name = next(notes).text
        field_verbose_name = next(notes).text

        unit = Unit(
            plugin_id=plugin_id,
            plugin_type=plugin_type if plugin_type else "",
            plugin_name=plugin_name if plugin_name else "",
            field_name=field_name,
            field_type=field_type,
            field_verbose_name=field_verbose_name,
            source=source,
            target=target,
            max_length=int(max_length) if max_length else None,
        )
        units.append(unit)
    return units


def parse_xliff_version_1_2(version: XliffVersion, xliff_element: Element) -> XliffContext:
    xml_namespaces = get_xliff_namespaces(version)

    file_element = xliff_element.find("file", namespaces=xml_namespaces)
    if file_element is None:
        raise XliffError("XLIFF Error: Missing file tag")

    source_language = file_element.attrib["source-language"]
    target_language = file_element.attrib["target-language"]
    page_path = file_element.attrib["original"]

    tool_element = file_element.find("tool", namespaces=xml_namespaces)
    if tool_element is None:
        raise XliffError("XLIFF Error: Missing <tool> in <file>")

    page_id = tool_element.attrib["tool-id"]

    body_element = file_element.find("body", namespaces=xml_namespaces)
    if body_element is None:
        raise XliffError("XLIFF Error: Missing <body> in <file>")

    units = _parse_xliff_units_version_1_2(xml_namespaces, body_element)

    return XliffContext(
        source_language=source_language,
        target_language=target_language,
        page_id=int(page_id),
        page_path=page_path,
        units=units,
    )


def parse_xliff_document(file) -> XliffContext:
    try:
        doc = parse(file)
    except ParseError:
        raise XliffError(_("Invalid xml"))

    xliff_element = doc.getroot()

    found_version = get_xliff_version(xliff_element.attrib["version"])

    if found_version == XliffVersion.V1_2:
        return parse_xliff_version_1_2(found_version, xliff_element)

    raise XliffConfigurationError(f"Missing parser function for version: {found_version.value}")
