import pprint

from django.conf import settings
from django.core.management import BaseCommand, CommandError

from djangocms_xliff.exceptions import XliffError
from djangocms_xliff.extractors import extract_units_from_obj
from djangocms_xliff.utils import get_obj, group_units_by_plugin_id


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("content_type_id", type=int)
        parser.add_argument("obj_id", type=int)
        parser.add_argument(
            "current_language",
            nargs="?",
            type=str,
            choices=[code for code, language in settings.LANGUAGES],
            default="de",
        )

    def handle(self, *args, **options):
        try:
            content_type_id = options["content_type_id"]
            obj_id = options["obj_id"]
            current_language = options["current_language"]

            obj = get_obj(content_type_id, obj_id)
            units = extract_units_from_obj(obj, current_language)

            self.stdout.write(
                self.style.SUCCESS(
                    f"Found {len(units)} xliff units on page with id: {obj.id} and language: {current_language}"
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
