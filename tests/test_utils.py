from unittest.mock import patch

from djangocms_xliff.settings import XLIFF_NAMESPACES, XliffVersion
from djangocms_xliff.utils import get_xliff_xml_namespaces


def test_multiple_xliff_xml_namespaces():
    version = XliffVersion.V1_2

    new_xliff_namespaces = {
        version: {"": "urn:oasis:names:tc:xliff:document:1.2", "test": "urn:oasis:names:tc:xliff:document:1.2:test"}
    }

    with patch.dict(XLIFF_NAMESPACES, new_xliff_namespaces):
        expected = {
            "xmlns": "urn:oasis:names:tc:xliff:document:1.2",
            "xmlns:test": "urn:oasis:names:tc:xliff:document:1.2:test",
        }
        assert get_xliff_xml_namespaces(version) == expected
