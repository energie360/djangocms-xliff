import json
from dataclasses import asdict

from django import forms
from django.conf import settings
from django.contrib import messages
from django.contrib.admin.templatetags.admin_urls import admin_urlname
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.translation import gettext as _

from djangocms_xliff.exceptions import XliffError, XliffImportError
from djangocms_xliff.extractors import extract_units_from_obj
from djangocms_xliff.imports import compare_units, save_xliff_context
from djangocms_xliff.parsers import parse_xliff_document
from djangocms_xliff.renderer import render_xliff_document
from djangocms_xliff.settings import TEMPLATES_FOLDER_ADMIN
from djangocms_xliff.types import XliffContext
from djangocms_xliff.utils import get_lang_name, get_xliff_version


class XliffExportForm(forms.Form):
    source_language = forms.ChoiceField(label=_("Source language:"))
    target_language = forms.ChoiceField(label=_("Target language:"))
    action = forms.CharField(widget=forms.HiddenInput(), initial="export")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        languages = list(settings.LANGUAGES)
        self.fields["source_language"].choices = languages
        self.fields["source_language"].initial = languages[0][0]
        self.fields["target_language"].choices = languages
        self.fields["target_language"].initial = languages[1][0] if len(languages) > 1 else languages[0][0]


class XliffImportForm(forms.Form):
    file = forms.FileField(label=_("File to import"))
    action = forms.CharField(widget=forms.HiddenInput(), initial="import")


class XliffImportExportMixin:
    change_list_template = f"{TEMPLATES_FOLDER_ADMIN}/change_list.html"

    def get_urls(self):
        from django.urls import path

        urls = super().get_urls()  # type: ignore
        info = self.get_model_info()
        my_urls = [
            path(
                "xliff/",
                self.admin_site.admin_view(self.xliff_overview_view),  # type: ignore
                name="{}_{}_xliff_overview".format(*info),
            ),
            path(
                "xliff/import/",
                self.admin_site.admin_view(self.xliff_import_view),  # type: ignore
                name="{}_{}_xliff_import".format(*info),
            ),
        ]
        return my_urls + urls

    def xliff_overview_view(self, request):
        export_form = XliffExportForm()
        import_form = XliffImportForm()

        if request.method == "POST":
            action = request.POST["action"]
            if action == "export":
                export_form = XliffExportForm(request.POST)
                if export_form.is_valid():
                    source_language = export_form.cleaned_data["source_language"]
                    target_language = export_form.cleaned_data["target_language"]
                    return self.handle_export(request, source_language, target_language)
            elif action == "import":
                import_form = XliffImportForm(request.POST, request.FILES)
                if import_form.is_valid():
                    return self.handle_import(request, import_form.cleaned_data["file"])

        context = {
            "title": _("XLIFF"),
            "export_form": export_form,
            "import_form": import_form,
            **self.admin_context(request),
        }
        return render(request, f"{TEMPLATES_FOLDER_ADMIN}/overview.html", context=context)

    def get_xliff_context(self, request, source_language: str, target_language: str) -> XliffContext:
        units = []

        for obj in self.get_queryset_with_filters(request):
            units.extend(extract_units_from_obj(obj=obj, language=source_language, allow_empty_plugins=True))

        return XliffContext(
            source_language=source_language,
            target_language=target_language,
            content_type_id=0,
            obj_id=0,
            path=request.path,
            units=units,
        )

    def handle_export(self, request, source_language: str, target_language: str):
        xliff_context = self.get_xliff_context(request, source_language, target_language)
        xliff_version = get_xliff_version("1.2")
        xliff_str = render_xliff_document(xliff_version, xliff_context)

        app_label, model_name = self.get_model_info()
        file_name = f"admin_{app_label}_{model_name}.xliff"

        return HttpResponse(
            content_type="application/xliff+xml",
            content=xliff_str,
            headers={"Content-Disposition": f"attachment; filename={file_name}"},
        )

    def handle_import(self, request, uploaded_file):
        try:
            xliff_context = parse_xliff_document(uploaded_file)
            database_xliff_context = self.get_xliff_context(
                request=request,
                source_language=xliff_context.source_language,
                target_language=xliff_context.target_language,
            )
            xliff_context.units = compare_units(xliff_context.units, database_xliff_context.units)

            if xliff_context.path != request.path:
                error_message = _('Selected page: "%(current_path)s" is not the same as xliff path: "%(xliff_path)s"')
                error_params = {"current_path": request.path, "xliff_path": xliff_context.path}
                raise XliffImportError(error_message % error_params)

            languages = dict(settings.LANGUAGES)
            if xliff_context.source_language not in languages:
                raise XliffImportError("Source language is not a supported language")

            if xliff_context.target_language not in languages:
                raise XliffImportError("Target language is not a supported language")

            return self.render_preview(request, xliff_context)
        except XliffError as e:
            return self.error_response(request, e)

    def render_preview(self, request, xliff_context: XliffContext):
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
            "xliff": xliff_context,
            "xliff_json": json.dumps(asdict(xliff_context)),
            **self.admin_context(request),
        }
        return render(request, f"{TEMPLATES_FOLDER_ADMIN}/preview.html", context)

    def error_response(self, request, message):
        context = {
            "title": _("XLIFF Error"),
            "message": message,
            **self.admin_context(request),
        }
        return render(request, f"{TEMPLATES_FOLDER_ADMIN}/error.html", context)

    def xliff_import_view(self, request):
        try:
            data = json.loads(request.POST["xliff_json"])
            xliff_context = XliffContext.from_dict(data)
            save_xliff_context(xliff_context)

            _, model_name = self.get_model_info()
            messages.add_message(request, messages.SUCCESS, f"Successfully updated: {model_name}")

            return redirect(reverse(admin_urlname(self.model._meta, "xliff_overview")))  # type: ignore
        except XliffError as e:
            return self.error_response(request, e)

    def admin_context(self, request):
        request.current_app = self.admin_site.name  # type: ignore
        return {"opts": self.model._meta, **self.admin_site.each_context(request)}  # type: ignore

    def get_model_info(self) -> tuple[str, str]:
        return self.model._meta.app_label, self.model._meta.model_name  # type: ignore

    def get_queryset_with_filters(self, request):
        """
        Returns queryset with filters set in the admin

        django-import-export uses this code:
        https://github.com/django-import-export/django-import-export/blob/main/import_export/admin.py#L716
        """
        list_display = self.get_list_display(request)  # type: ignore
        if self.get_actions(request):  # type: ignore
            list_display = ["action_checkbox"] + list(list_display)

        ChangeList = self.get_changelist(request)  # type: ignore
        changelist_kwargs = {
            "request": request,
            "model": self.model,  # type: ignore
            "list_display": list_display,
            "list_display_links": self.get_list_display_links(request, list_display),  # type: ignore
            "list_filter": self.get_list_filter(request),  # type: ignore
            "date_hierarchy": self.date_hierarchy,  # type: ignore
            "search_fields": self.get_search_fields(request),  # type: ignore
            "list_select_related": self.get_list_select_related(request),  # type: ignore
            "list_per_page": self.list_per_page,  # type: ignore
            "list_max_show_all": self.list_max_show_all,  # type: ignore
            "list_editable": self.list_editable,  # type: ignore
            "model_admin": self,
            "sortable_by": self.sortable_by,  # type: ignore
        }
        import django

        if django.VERSION >= (4, 0):
            changelist_kwargs["search_help_text"] = self.search_help_text  # type: ignore

        cl = ChangeList(**changelist_kwargs)
        return cl.get_queryset(request)
