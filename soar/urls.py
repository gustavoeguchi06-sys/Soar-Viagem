from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    # O painel do dono do site: cadastrar destinos, fotos, roteiro, hospedagens
    # e acompanhar as reservas. Só entra quem tem conta de equipe (is_staff).
    #
    # Não existe mais rota em /admin/: ela redirecionava para cá e entregava o
    # painel ao primeiro scanner que batesse no endereço padrão, o que anulava
    # o motivo de ter renomeado. Renomear não é proteção — a proteção é limite
    # de tentativa no login, e restringir este caminho por IP ou VPN.
    path('painel/', admin.site.urls),
    path('', include('contas.urls')),
    path('', include('reservas.urls')),
    path('blog/', include('blog.urls')),
    path('', include('destinations.urls')),
]

# Em modo DEBUG, o próprio Django serve as imagens enviadas (pasta media/).
# Em produção quem serve é o Nginx — veja o bloco documentado no README, que
# inclui o nosniff e o Content-Disposition que o Django não tem como aplicar
# em arquivo servido direto pelo servidor web.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
