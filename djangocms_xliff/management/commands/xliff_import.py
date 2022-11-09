from pathlib import Path

from django.core.management import BaseCommand, CommandError

from djangocms_xliff.exceptions import XliffError
from djangocms_xliff.imports import save_xliff_context
from djangocms_xliff.parsers import parse_xliff_document


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("file_name", type=str)

    def handle(self, *args, **options):
        try:
            import_file = Path(options["file_name"])

            with import_file.open("r") as xliff_file:
                xliff_context = parse_xliff_document(xliff_file)
                self.stdout.write(f"Found {len(xliff_context.units)} xliff units in {import_file.resolve()}")

                wants_to_continue = input(
                    "Do you want to import the units? This will save them directly into the database. (y/n): "
                )
                if wants_to_continue == "y":
                    save_xliff_context(xliff_context)

                    self.stdout.write(
                        self.style.SUCCESS(
                            f"Successfully imported {len(xliff_context.units)} units for "
                            f"page with id: {xliff_context.page_id} "
                            f"and language: {xliff_context.target_language}"
                        )
                    )
                    self.stdout.write(
                        f"Path to page: {xliff_context.page.get_absolute_url(xliff_context.target_language)}"
                    )
                else:
                    raise CommandError("Aborted.")
        except XliffError as e:
            raise CommandError(e)
