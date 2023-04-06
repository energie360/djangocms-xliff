from unittest.mock import patch

import pytest
from cms.api import create_page

from djangocms_xliff.exceptions import XliffError
from djangocms_xliff.settings import XLIFF_NAMESPACES, XliffVersion
from djangocms_xliff.utils import get_draft_page, get_xliff_xml_namespaces


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


@pytest.mark.django_db
def test_get_draft_page_id_must_be_a_draft():
    page = create_page("Test", "testing.html", "de", published=True)
    public_page = page.get_public_object()

    with pytest.raises(XliffError):
        get_draft_page(public_page.pk)
