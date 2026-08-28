from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from destinations.models import Destino


class Avaliacao(models.Model):
    destino = models.ForeignKey(Destino, on_delete=models.CASCADE,
                                related_name='avaliacoes', verbose_name='Destino')
    nome_autor = models.CharField('Seu nome', max_length=80)
    nota = models.PositiveSmallIntegerField(
        'Nota (1 a 5)',
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        default=5,
    )
    comentario = models.TextField('Comentário')
    foto = models.ImageField('Foto da viagem (opcional)', upload_to='avaliacoes/',
                             blank=True, null=True)
    criado_em = models.DateTimeField('Criado em', auto_now_add=True)

    class Meta:
        verbose_name = 'Avaliação'
        verbose_name_plural = 'Avaliações'
        ordering = ['-criado_em']

    def __str__(self):
        return f'{self.nome_autor} — {self.destino.nome} ({self.nota}/5)'

    @property
    def estrelas(self):
        """Retorna algo como '★★★★☆' para usar nos templates."""
        return '★' * self.nota + '☆' * (5 - self.nota)
