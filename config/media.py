"""Development media serving that the frontend PDF viewer may embed in an iframe."""

from django.conf import settings
from django.views.decorators.clickjacking import xframe_options_exempt
from django.views.static import serve


@xframe_options_exempt
def serve_media(request, path):
    response = serve(request, path, document_root=settings.MEDIA_ROOT)
    ancestors = " ".join(["'self'", *settings.FRONTEND_ORIGINS])
    response["Content-Security-Policy"] = f"frame-ancestors {ancestors}"
    return response
