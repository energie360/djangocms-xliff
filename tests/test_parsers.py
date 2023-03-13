import io

from cms.models import Page
from django.contrib.contenttypes.models import ContentType

from djangocms_xliff.parsers import parse_xliff_document
from djangocms_xliff.types import Unit


def test_parse_xliff_version_1_2_simple(create_xliff_page_context):
    content_type_id = ContentType.objects.get_for_model(Page).id
    file_content = f"""<?xml version="1.0" encoding="utf-8" standalone="no"?>
        <xliff xmlns="urn:oasis:names:tc:xliff:document:1.2" version="1.2">
            <file original="test" datatype="plaintext" source-language="en" target-language="de">
                <tool tool-id="{content_type_id}__1" tool-name="djangocms_xliff" tool-company-name="Energie 360°"/>
                <body>
                    <trans-unit id="123__title" resname="123__title" maxwidth="30" size-unit="char" extype="django.db.models.CharField">
                        <note>TestPlugin</note>
                        <note>Test Plugin</note>
                        <note>Title</note>
                        <source><![CDATA[Welcome]]></source>
                        <target><![CDATA[Willkommen]]></target>
                    </trans-unit>
                </body>
            </file>
        </xliff>
    """
    file_buffer = io.StringIO(file_content)

    expected = create_xliff_page_context(
        units=[
            Unit(
                plugin_id=123,
                plugin_type="TestPlugin",
                plugin_name="Test Plugin",
                field_name="title",
                field_type="django.db.models.CharField",
                field_verbose_name="Title",
                source="Welcome",
                target="Willkommen",
                max_length=30,
            )
        ],
        obj_id=1,
        path="test",
        source_language="en",
        target_language="de",
    )

    assert parse_xliff_document(file_buffer) == expected


def test_parse_xliff_version_1_2_utf_8_characters(create_xliff_page_context):
    content_type_id = ContentType.objects.get_for_model(Page).id
    file_content = f"""<?xml version="1.0" encoding="utf-8" standalone="no"?>
        <xliff xmlns="urn:oasis:names:tc:xliff:document:1.2" version="1.2">
            <file original="test/example" datatype="plaintext" source-language="de" target-language="fr">
                <tool tool-id="{content_type_id}__1" tool-name="djangocms_xliff" tool-company-name="Energie 360°" />
                <body>
                    <trans-unit id="5917__title" resname="5917__title" maxwidth="60" size-unit="char" extype="django.db.models.CharField">
                        <source><![CDATA[Willkommen]]></source>
                        <target><![CDATA[Accueillir]]></target>
                        <note>TestBlockPlugin</note>
                        <note>Test Block Plugin</note>
                        <note>Title</note>
                    </trans-unit>
                    <trans-unit id="5918__title" resname="5918__title" maxwidth="35" size-unit="char" extype="django.db.models.CharField">
                        <source><![CDATA[Das ist ein Beispiel]]></source>
                        <target><![CDATA[This is an example]]></target>
                        <note>TestBlockSlidePlugin</note>
                        <note>Test Block Slide Plugin</note>
                        <note>Title</note>
                    </trans-unit>
                </body>
            </file>
        </xliff>
    """
    file_buffer = io.StringIO(file_content)

    expected = create_xliff_page_context(
        units=[
            Unit(
                plugin_id=5917,
                plugin_type="TestBlockPlugin",
                plugin_name="Test Block Plugin",
                field_name="title",
                field_type="django.db.models.CharField",
                field_verbose_name="Title",
                source="Willkommen",
                target="Accueillir",
                max_length=60,
            ),
            Unit(
                plugin_id=5918,
                plugin_type="TestBlockSlidePlugin",
                plugin_name="Test Block Slide Plugin",
                field_name="title",
                field_type="django.db.models.CharField",
                field_verbose_name="Title",
                source="Das ist ein Beispiel",
                target="This is an example",
                max_length=35,
            ),
        ],
        path="test/example",
        obj_id=1,
        source_language="de",
        target_language="fr",
    )

    assert parse_xliff_document(file_buffer) == expected


def test_parse_xliff_version_1_2_html(create_xliff_page_context):
    content_type_id = ContentType.objects.get_for_model(Page).id
    file_content = f"""<?xml version="1.0" encoding="utf-8" standalone="no"?>
        <xliff xmlns="urn:oasis:names:tc:xliff:document:1.2" version="1.2">
            <file original="test/example" datatype="plaintext" source-language="de" target-language="fr">
                <tool tool-id="{content_type_id}__2" tool-name="djangocms_xliff" tool-company-name="Energie 360°" />
                <body>
                    <trans-unit id="6008__body" resname="6008__body" extype="django.db.models.CharField">
                        <source><![CDATA[<h2>Willkommen</h2>
<h3>Das ist ein Beispieltext</h3>
<p>Welche funktionen bietet das XLIFF package?</p>
<ul>
    <li>Export einer CMS Seite als XLIFF</li>
    <li>Import der XLIFF Datei mit einer Vorschau</li>
</ul>
<p>Bitte beachten Sie, dass komplexe Typen, Bilder, Medien und Links nicht Teil des Übersetzungsprozesses sind und manuell übersetzt werden müssen.</p>]]></source>
                    <target><![CDATA[<h2>Bienvenue</h2>
<h3>Ceci est un exemple de texte</h3>
<p>Quelles sont les fonctions offertes par le package XLIFF?</p>
<ul>
    <li>Exporter une page CMS au format XLIFF</li>
    <li>Importer le fichier XLIFF avec un aperçu</li>
</ul>
<p>Veuillez noter que les types complexes, les images, les médias et les liens ne font pas partie du processus de traduction et doivent être traduits manuellement.</p>]]></target>
                        <note>Richtext</note>
                        <note>Richtext</note>
                        <note>Body</note>
                    </trans-unit>
                </body>
            </file>
        </xliff>
    """
    file_buffer = io.StringIO(file_content)

    expected = create_xliff_page_context(
        units=[
            Unit(
                plugin_id=6008,
                plugin_type="Richtext",
                plugin_name="Richtext",
                field_name="body",
                field_type="django.db.models.CharField",
                field_verbose_name="Body",
                source="""<h2>Willkommen</h2>\n<h3>Das ist ein Beispieltext</h3>\n<p>Welche funktionen bietet das XLIFF package?</p>\n<ul>\n    <li>Export einer CMS Seite als XLIFF</li>\n    <li>Import der XLIFF Datei mit einer Vorschau</li>\n</ul>\n<p>Bitte beachten Sie, dass komplexe Typen, Bilder, Medien und Links nicht Teil des Übersetzungsprozesses sind und manuell übersetzt werden müssen.</p>""",
                target="""<h2>Bienvenue</h2>\n<h3>Ceci est un exemple de texte</h3>\n<p>Quelles sont les fonctions offertes par le package XLIFF?</p>\n<ul>\n    <li>Exporter une page CMS au format XLIFF</li>\n    <li>Importer le fichier XLIFF avec un aperçu</li>\n</ul>\n<p>Veuillez noter que les types complexes, les images, les médias et les liens ne font pas partie du processus de traduction et doivent être traduits manuellement.</p>""",
            ),
        ],
        path="test/example",
        obj_id=2,
        source_language="de",
        target_language="fr",
    )

    assert parse_xliff_document(file_buffer) == expected
