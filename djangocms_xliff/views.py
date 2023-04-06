import json
from dataclasses import asdict
from typing import Type

from cms.models import Page
from django.contrib.admin import site
from django.contrib.admin.views.decorators import staff_member_required
from django.forms import Form
from django.http import HttpResponse
from django.shortcuts import render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.translation import gettext as _
from django.views import View

from djangocms_xliff.exceptions import XliffError
from djangocms_xliff.exports import export_page_as_xliff
from djangocms_xliff.forms import ExportForm, UploadFileForm
from djangocms_xliff.imports import save_xliff_context, validate_xliff
from djangocms_xliff.parsers import parse_xliff_document
from djangocms_xliff.settings import (
    TEMPLATES_FOLDER,
    TEMPLATES_FOLDER_EXPORT,
    TEMPLATES_FOLDER_IMPORT,
)
from djangocms_xliff.types import Unit, XliffContext
from djangocms_xliff.utils import get_draft_page, get_lang_name


class XliffView(View):
    template: str
    form_class: Type[Form]

    def error_response(self, message):
        return render(
            self.request,
            f"{TEMPLATES_FOLDER}/error.html",
            context={"message": message},
        )


@method_decorator(staff_member_required, name="dispatch")
class ExportView(XliffView):
    template = f"{TEMPLATES_FOLDER_EXPORT}/index.html"
    form_class: Type[ExportForm] = ExportForm

    def get(self, request, page_id: int, current_language: str, *args, **kwargs):
        form = self.form_class(current_language)
        return self.render_template(form, current_language)

    def post(self, request, page_id: int, current_language: str, *args, **kwargs):
        form = self.form_class(current_language, request.POST)
        if not form.is_valid():
            return self.render_template(form, current_language)

        try:
            xliff_str, file_name = export_page_as_xliff(
                page_id=page_id,
                source_language=form.cleaned_data["source_language"],
                target_language=current_language,
            )
        except XliffError as e:
            return self.error_response(e)

        return HttpResponse(
            content_type="application/xliff+xml",
            content=xliff_str,
            headers={"Content-Disposition": f"attachment; filename={file_name}"},
        )

    def render_template(self, form: Form, current_language: str):
        lead_params = {"language": get_lang_name(current_language)}
        lead = _('Export the content of the currently selected language "%(language)s".') % lead_params

        line1_params = {"import_from": _("Import from XLIFF")}
        line1 = (
            _('Translate this file in your preferred XLIFF tool and import later on with "%(import_from)s".')
            % line1_params
        )

        context = {
            "title": _("Export"),
            "form": form,
            "lead": lead,
            "line1": line1,
            "line2": _("You can only import the exact file and language you've exported."),
            "line3": _(
                "First create the page to be translated in the new language, "
                "copy the plugins and only then create an export."
            ),
            "button_label": _("Download"),
        }
        return render(self.request, self.template, context)


@method_decorator(staff_member_required, name="dispatch")
class UploadView(XliffView):
    template = f"{TEMPLATES_FOLDER_IMPORT}/upload.html"
    template_success = f"{TEMPLATES_FOLDER_IMPORT}/preview.html"
    form_class: Type[UploadFileForm] = UploadFileForm

    def get(self, request, page_id, current_language: str, *args, **kwargs):
        form = self.form_class()
        return self.render_template(form, current_language)

    def post(self, request, page_id, current_language, *args, **kwargs):
        form = self.form_class(request.POST, request.FILES)
        if not form.is_valid():
            return self.render_template(form, current_language)

        try:
            uploaded_file = form.cleaned_data["file"]
            xliff_context = parse_xliff_document(uploaded_file)

            page = get_draft_page(page_id)
            validate_xliff(page, xliff_context, current_language)

            return self.render_template_success(uploaded_file.name, xliff_context)
        except XliffError as e:
            return self.error_response(e)

    def render_template(self, form: Form, current_language: str):
        lead_params = {"language": get_lang_name(current_language)}
        context = {
            "title": _("Import"),
            "lead": _('Import the translation for the "%(language)s" page.') % lead_params,
            "description": _("You can only import to the same page and language you exported from."),
            "form": form,
            "button_label": _("Preview"),
        }
        return render(self.request, self.template, context)

    def render_template_success(self, file_name: str, xliff_context: XliffContext):
        description_params = {
            "language": get_lang_name(xliff_context.target_language),
            "count_plugins": len(xliff_context.units),
        }
        description = (
            _('Found %(count_plugins)d plugins that will be imported to the "%(language)s" page.') % description_params
        )

        note = _(
            "Please note that complex types, images, media and links are not part of the translation "
            "process and have to be translated manually."
        )

        context = {
            "description": description,
            "note": note,
            "action_url": reverse(
                "djangocms_xliff:import",
                kwargs={
                    "page_id": xliff_context.page_id,
                    "current_language": xliff_context.target_language,
                },
            ),
            "xliff": xliff_context,
            "xliff_json": json.dumps(asdict(xliff_context)),
        }
        return render(self.request, self.template_success, context)


@method_decorator(staff_member_required, name="dispatch")
class ImportView(XliffView):
    def post(self, request, page_id, current_language, *args, **kwargs):
        try:
            data = json.loads(request.POST["xliff_json"])
            units = data.pop("units", [])

            xliff_context = XliffContext(**data, units=[Unit(**u) for u in units])
            save_xliff_context(xliff_context)

            admin = site._registry[Page]
            return admin.response_change(request, xliff_context.page)
        except XliffError as e:
            return self.error_response(e)
