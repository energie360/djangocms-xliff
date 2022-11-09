from django import forms
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class ExportForm(forms.Form):
    source_language = forms.ChoiceField(
        label=_("Source language in XLIFF header:"),
        help_text=_(
            "The source language is usually the main language of the project. "
            "It serves as an orientation for the translator in the XLIFF tool."
        ),
    )

    def __init__(self, current_language: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["source_language"].choices = [  # type: ignore
            (code, name) for code, name in settings.LANGUAGES if code != current_language
        ]


class UploadFileForm(forms.Form):
    file = forms.FileField(label=_("File to import"))
