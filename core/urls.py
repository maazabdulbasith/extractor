from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', lambda request: JsonResponse({"status": "ok", "endpoints": ["/api/health", "/api/extractor/upload/"]})),
    path('api/health', lambda request: JsonResponse({"status": "ok"})),
    path('api/extractor/', include('extractor.urls')),
    path('api/nlp/', include('nlp.urls')),  # future
    path('api/db/', include('db.urls')),    # future
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
