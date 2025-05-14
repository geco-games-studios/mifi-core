from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static

from mifi import settings

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/test/v1/', include('apis.urls'))
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

