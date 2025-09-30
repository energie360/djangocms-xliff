import abc
from typing import TYPE_CHECKING

from cms.models import Page
from defusedxml.ElementTree import ParseError, parse
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import gettext

from djangocms_xliff.exceptions import XliffConfigurationError, XliffError
from djangocms_xliff.settings import UNIT_ID_DELIMITER, XliffVersion
from djangocms_xliff.types import Unit, XliffContext
from djangocms_xliff.utils import get_xliff_namespaces, get_xliff_version

if TYPE_CHECKING:
    from xml.etree.ElementTree import Element  # nosec


class VersionParser(abc.ABC):
    def __init__(self, xliff_element: "Element", xml_namespaces: dict):
        self.xliff_element = xliff_element
        self.xml_namespaces = xml_namespaces

    @abc.abstractmethod
    def parse(self) -> XliffContext:
        raise NotImplementedError()


class Version12(VersionParser):
    def __init__(self, xliff_element: "Element", xml_namespaces: dict):
        super().__init__(xliff_element, xml_namespaces)

        file_element = xliff_element.find("file", namespaces=self.xml_namespaces)
        if file_element is None:
            raise XliffError("XLIFF Error: Missing file tag")

        body_element = file_element.find("body", namespaces=self.xml_namespaces)
        if body_element is None:
            raise XliffError("XLIFF Error: Missing <body> in <file>")

        self.file_element: Element = file_element
        self.body_element: Element = body_element

    def parse_file_element(self) -> tuple[str, str, str]:
        file_element = self.xliff_element.find("file", namespaces=self.xml_namespaces)
        if file_element is None:
            raise XliffError("XLIFF Error: Missing file tag")

        source_language = file_element.attrib["source-language"]
        target_language = file_element.attrib["target-language"]
        path = file_element.attrib["original"]

        tool_element = file_element.find("tool", namespaces=self.xml_namespaces)
        if tool_element is None:
            raise XliffError("XLIFF Error: Missing <tool> in <file>")

        return source_language, target_language, path

    def parse_tool_element(self) -> tuple[int, int]:
        tool_element = self.file_element.find("tool", namespaces=self.xml_namespaces)
        if tool_element is None:
            raise XliffError("XLIFF Error: Missing <tool> in <file>")

        content_type_id: str | int
        try:
            content_type_id, obj_id = tool_element.attrib["tool-id"].split(UNIT_ID_DELIMITER)
        except ValueError:
            # For backwards compatibility, if there are existing xliff files
            # with just the page_id as the tool-id
            obj_id = tool_element.attrib["tool-id"]
            content_type_id = ContentType.objects.get_for_model(Page).pk

        return int(content_type_id), int(obj_id)

    def parse_body_element(self):
        units = []
        for trans_unit in self.body_element.findall("trans-unit", namespaces=self.xml_namespaces):
            unit_id = trans_unit.attrib["id"]
            plugin_id, field_name = unit_id.rsplit(UNIT_ID_DELIMITER, 1)

            field_type = trans_unit.attrib["extype"]

            max_length = trans_unit.attrib.get("maxwidth")

            source_element = trans_unit.find("source", namespaces=self.xml_namespaces)
            if source_element is None:
                raise XliffError("XLIFF Error: Missing <source> in <trans-unit>")

            target_element = trans_unit.find("target", namespaces=self.xml_namespaces)
            if target_element is None:
                raise XliffError("XLIFF Error: Missing <target> in <trans-unit>")

            source = source_element.text if source_element.text else ""
            target = target_element.text if target_element.text else source

            notes = trans_unit.iterfind("note", namespaces=self.xml_namespaces)
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

    def parse(self) -> XliffContext:
        source_language, target_language, path = self.parse_file_element()
        content_type_id, obj_id = self.parse_tool_element()
        units = self.parse_body_element()

        return XliffContext(
            source_language=source_language,
            target_language=target_language,
            content_type_id=content_type_id,
            obj_id=obj_id,
            path=path,
            units=units,
        )


def parse_xliff_document(file) -> XliffContext:
    try:
        doc = parse(file)
    except ParseError as e:
        raise XliffError(gettext("Invalid xml")) from e

    xliff_element = doc.getroot()

    found_version = get_xliff_version(xliff_element.attrib["version"])  # type: ignore
    xml_namespaces = get_xliff_namespaces(found_version)

    parser: VersionParser | None = None
    if found_version == XliffVersion.V1_2:
        parser = Version12(xliff_element, xml_namespaces)  # type: ignore

    if parser is None:
        raise XliffConfigurationError(f"Missing VersionParser for version: {found_version.value}")

    return parser.parse()
