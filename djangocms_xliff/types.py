from dataclasses import dataclass
from typing import Any

from cms.models import PageContent
from django.db.models import Model
from django.utils.translation import gettext
from djangocms_alias.models import AliasContent

ExportContent = str
ExportFileName = str
ExportPage = tuple[ExportContent, ExportFileName]

type XliffObj[DjangoModelType: Model] = PageContent | AliasContent | DjangoModelType


@dataclass
class Unit:
    plugin_id: str
    plugin_type: str
    plugin_name: str

    field_name: str
    field_type: str

    source: str
    target: str = ""

    field_verbose_name: str | None = None
    max_length: int | None = None

    @property
    def id(self):
        from djangocms_xliff.utils import get_unit_id_format

        return get_unit_id_format(self.plugin_id, self.field_name)

    @property
    def notes(self) -> list[str | None]:
        notes = [
            self.plugin_type,
            self.plugin_name,
            self.field_verbose_name,
        ]
        if self.max_length:
            notes.append(gettext("Max characters: %(max_length)d") % {"max_length": self.max_length})
        return notes

    @property
    def target_length(self) -> int:
        return len(self.target)

    def is_max_length_exceeded(self) -> bool:
        if self.max_length is None:
            # if max_length is None, then there is no limit
            return False

        return self.target_length > self.max_length


@dataclass
class XliffContext:
    source_language: str
    target_language: str
    content_type_id: int
    obj_id: Any
    path: str
    units: list[Unit]

    @property
    def grouped_units(self) -> list[tuple[str, list[Unit]]]:
        from djangocms_xliff.utils import group_units_by_plugin_id

        return group_units_by_plugin_id(self.units)

    @property
    def tool_id(self) -> str:
        from djangocms_xliff.utils import get_unit_id_format

        return get_unit_id_format(self.content_type_id, self.obj_id)

    @classmethod
    def from_dict(cls, data: dict) -> "XliffContext":
        units = data.pop("units", [])
        return cls(**data, units=[Unit(**u) for u in units])

    def get_obj(self) -> XliffObj:
        from djangocms_xliff.utils import get_obj

        return get_obj(self.content_type_id, self.obj_id)
