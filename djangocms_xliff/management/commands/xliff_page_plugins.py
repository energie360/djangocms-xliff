import pprint

from django.conf import settings
from django.core.management import BaseCommand, CommandError

from djangocms_xliff.exceptions import XliffError
from djangocms_xliff.extractors import extract_units_from_page
from djangocms_xliff.utils import get_draft_page, group_units_by_plugin_id


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("page_id", type=int)
        parser.add_argument(
            "current_language",
            nargs="?",
            type=str,
            choices=[code for code, language in settings.LANGUAGES],
            default="de",
        )

    def handle(self, *args, **options):
        try:
            page_id = options["page_id"]
            current_language = options["current_language"]

            page = get_draft_page(page_id)
            units = extract_units_from_page(page, current_language)

            self.stdout.write(
                self.style.SUCCESS(
                    f"Found {len(units)} xliff units on page with id: {page.pk} and language: {current_language}"
                )
            )
            self.stdout.write()

            for plugin_id, units in group_units_by_plugin_id(units):
                self.stdout.write(f"Plugin: {plugin_id}")
                self.stdout.write()
                for unit in units:
                    pprint.pprint(unit)
                self.stdout.write()
                self.stdout.write()

        except XliffError as e:
            raise CommandError(e)
