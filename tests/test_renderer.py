from cms.models import Page
from django.contrib.contenttypes.models import ContentType

from djangocms_xliff.renderer import render_xliff_document
from djangocms_xliff.settings import XliffVersion
from djangocms_xliff.types import Unit


def test_create_xliff_version_1_2_simple(create_xliff_page_context):
    units = [
        Unit(
            plugin_id=123,
            plugin_type="TestPlugin",
            plugin_name="Test Plugin",
            field_name="title",
            field_verbose_name="Title",
            field_type="django.db.models.CharField",
            source="Willkommen",
            target="",
            max_length=30,
        )
    ]

    xliff_context = create_xliff_page_context(units)

    content_type_id = ContentType.objects.get_for_model(Page).id

    expected = f"""<?xml version="1.0" encoding="utf-8" standalone="no"?>
<xliff xmlns="urn:oasis:names:tc:xliff:document:1.2" version="1.2">
    <file original="/test" datatype="plaintext" source-language="de" target-language="fr">
        <tool tool-id="{content_type_id}__1" tool-name="djangocms_xliff" tool-company-name="Energie 360°"/>
        <body>
            <trans-unit id="123__title" resname="123__title" maxwidth="30" size-unit="char" extype="django.db.models.CharField">
                <source><![CDATA[Willkommen]]></source>
                <target><![CDATA[]]></target>
                <note>TestPlugin</note>
                <note>Test Plugin</note>
                <note>Title</note>
                <note>Max characters: 30</note>
            </trans-unit>
        </body>
    </file>
</xliff>

"""

    assert render_xliff_document(XliffVersion.V1_2, xliff_context) == expected
