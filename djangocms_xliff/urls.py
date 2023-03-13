from django.urls import path

from djangocms_xliff.views import ExportView, ImportView, UploadView

app_name = "djangocms_xliff"

urlpatterns = [
    path(
        "export/<int:content_type_id>/<int:obj_id>/<str:current_language>/",
        ExportView.as_view(),
        name="export",
    ),
    path(
        "upload/<int:content_type_id>/<int:obj_id>/<str:current_language>/",
        UploadView.as_view(),
        name="upload",
    ),
    path(
        "import/<int:content_type_id>/<int:obj_id>/<str:current_language>/",
        ImportView.as_view(),
        name="import",
    ),
]
