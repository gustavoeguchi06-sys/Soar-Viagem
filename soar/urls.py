from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

urlpatterns = [
    # O painel do dono do site: cadastrar destinos, fotos, roteiro, hospedagens
    # e acompanhar as reservas. Só entra quem tem conta de equipe (is_staff).
    path('painel/', admin.site.urls),
    path('admin/', RedirectView.as_view(url='/painel/', permanent=False)),
    path('', include('contas.urls')),
    path('', include('reservas.urls')),
    path('', include('destinations.urls')),
]

# Em modo DEBUG, o próprio Django serve as imagens enviadas (pasta media/)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

admin.site.site_header = 'Soar — Painel do dono'
admin.site.site_title = 'Soar'
admin.site.index_title = 'Gerenciar o site de viagem'
