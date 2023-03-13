from dataclasses import dataclass
from typing import List, Optional, Tuple, Union, Type

from cms.models import Page
from django.db.models import Model
from django.utils.translation import gettext as _

ID_DELIMITER = "__"

ExportContent = str
ExportFileName = str
ExportPage = Tuple[ExportContent, ExportFileName]
XliffObj = Union[Page, Type[Model]]


@dataclass
class Unit:
    plugin_id: int
    plugin_type: str
    plugin_name: str

    field_name: str
    field_type: str

    source: str
    target: str = ""

    field_verbose_name: Optional[str] = None
    max_length: Optional[int] = None

    @property
    def id(self):
        return f"{self.plugin_id}{ID_DELIMITER}{self.field_name}"

    @property
    def notes(self) -> List[Optional[str]]:
        notes = [
            self.plugin_type,
            self.plugin_name,
            self.field_verbose_name,
        ]
        if self.max_length:
            notes.append(_("Max characters: %(max_length)d") % {"max_length": self.max_length})
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
    obj_id: int
    path: str
    units: List[Unit]

    @property
    def grouped_units(self) -> List[Tuple[int, List[Unit]]]:
        from djangocms_xliff.utils import group_units_by_plugin_id

        return group_units_by_plugin_id(self.units)

    @property
    def tool_id(self) -> str:
        return f'{self.content_type_id}{ID_DELIMITER}{self.obj_id}'
