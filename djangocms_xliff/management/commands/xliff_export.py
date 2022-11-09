from pathlib import Path

from django.conf import settings
from django.core.management import BaseCommand, CommandError

from djangocms_xliff.exceptions import XliffError
from djangocms_xliff.exports import export_page_as_xliff


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("page_id", type=int)
        parser.add_argument(
            "xliff_source_language",
            type=str,
            choices=[code for code, language in settings.LANGUAGES],
        )
        parser.add_argument(
            "target_language",
            type=str,
            choices=[code for code, language in settings.LANGUAGES],
        )

    def handle(self, *args, **options):
        try:
            page_id = options["page_id"]
            xliff_source_language = options["xliff_source_language"]
            target_language = options["target_language"]

            if xliff_source_language == target_language:
                raise CommandError("xliff source language and current language should not be the same")

            xliff_str, file_name = export_page_as_xliff(
                page_id=page_id,
                source_language=xliff_source_language,
                target_language=target_language,
            )

            exported_file = Path(file_name)
            with exported_file.open("w") as translation_file:
                translation_file.write(xliff_str)

            self.stdout.write(self.style.SUCCESS(f"Successfully exported xliff file: {exported_file.resolve()}"))
        except XliffError as e:
            raise CommandError(e)
