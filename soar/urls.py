from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('destinations.urls')),
]

# Em modo DEBUG, o próprio Django serve as imagens enviadas (pasta media/)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

admin.site.site_header = 'Soar — Administração'
admin.site.site_title = 'Soar'
admin.site.index_title = 'Gerenciar o site de viagem'
