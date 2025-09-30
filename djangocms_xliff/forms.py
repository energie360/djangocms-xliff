from django import forms
from django.conf import settings
from django.utils.translation import gettext_lazy


class ExportForm(forms.Form):
    source_language = forms.ChoiceField(
        label=gettext_lazy("Source language in XLIFF header:"),
        help_text=gettext_lazy(
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
    file = forms.FileField(label=gettext_lazy("File to import"))
