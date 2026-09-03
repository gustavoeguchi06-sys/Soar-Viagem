from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from destinations.models import Destino


class AvaliacaoQuerySet(models.QuerySet):
    def publicadas(self):
        return self.filter(publicada=True)


class Avaliacao(models.Model):
    """Avaliação de um destino, escrita por um cliente com conta.

    Três coisas aqui existem por causa de segurança, não de produto:

    `autor` — antes qualquer visitante postava com o nome que quisesse, e dava
    para assinar "Soar Operadora". Agora o nome sai da conta.

    `publicada` — a avaliação entra na fila e só aparece no site depois que o
    dono aprova no painel. Sem isso, a nota da vitrine é editável por qualquer
    pessoa da internet.

    `ip` / `criado_em` — o mínimo para responder "quem escreveu isto?" quando
    aparece difamação ou spam.
    """

    destino = models.ForeignKey(Destino, on_delete=models.CASCADE,
                                related_name='avaliacoes', verbose_name='Destino')
    autor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                              null=True, blank=True, related_name='avaliacoes',
                              verbose_name='Cliente')
    nome_autor = models.CharField('Nome exibido', max_length=80,
                                  help_text='Preenchido a partir da conta de quem avaliou.')
    nota = models.PositiveSmallIntegerField(
        'Nota (1 a 5)',
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        default=5,
    )
    comentario = models.TextField('Comentário')
    foto = models.ImageField('Foto da viagem (opcional)', upload_to='avaliacoes/',
                             blank=True, null=True)
    publicada = models.BooleanField(
        'Publicada', default=False,
        help_text='Enquanto estiver desmarcada, a avaliação não aparece no site.')
    ip = models.GenericIPAddressField('IP de origem', blank=True, null=True,
                                      help_text='Registrado no envio, para apuração de abuso.')
    criado_em = models.DateTimeField('Criado em', auto_now_add=True)

    objects = AvaliacaoQuerySet.as_manager()

    class Meta:
        verbose_name = 'Avaliação'
        verbose_name_plural = 'Avaliações'
        ordering = ['-criado_em']
        constraints = [
            # Uma avaliação por pessoa por destino. Sem isto, uma conta só
            # empilha nota até mover a média sozinha.
            models.UniqueConstraint(
                fields=['destino', 'autor'],
                condition=models.Q(autor__isnull=False),
                name='uma_avaliacao_por_pessoa_por_destino',
            ),
        ]

    def __str__(self):
        return f'{self.nome_autor} — {self.destino.nome} ({self.nota}/5)'

    @property
    def estrelas(self):
        """Retorna algo como '★★★★☆' para usar nos templates."""
        return '★' * self.nota + '☆' * (5 - self.nota)
