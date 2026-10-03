"""Apaga do armazenamento (disco ou Cloudflare R2) os arquivos que ficaram sem uso.

O Django não apaga o arquivo quando o registro é apagado, nem o antigo quando
a foto é trocada no painel: com o tempo o disco da VPS (ou o bucket do R2)
enche de foto e vídeo que nenhuma página mostra. Aqui, para todo campo de
arquivo dos apps do projeto:

- apagou o registro: o arquivo dele vai embora;
- trocou ou limpou a foto/vídeo: o arquivo antigo vai embora.

Só depois que a transação do banco confirma (on_commit): se o salvar der erro,
nada é apagado. E nunca apaga um arquivo que outro registro ainda usa.
"""
import logging

from django.apps import apps
from django.db import models, transaction

log = logging.getLogger('soar.arquivos')

APPS = ('destinations', 'blog', 'reviews', 'agencia', 'contas', 'reservas')


def _campos(modelo):
    return [c for c in modelo._meta.get_fields() if isinstance(c, models.FileField)]


def _ainda_usado(nome):
    for modelo in apps.get_models():
        if modelo._meta.app_label not in APPS:
            continue
        for campo in _campos(modelo):
            if modelo._default_manager.filter(**{campo.name: nome}).exists():
                return True
    return False


def _apagar_depois(campo, nome):
    if not nome:
        return
    storage = campo.storage

    def apagar():
        if _ainda_usado(nome):
            return
        try:
            storage.delete(nome)
        except Exception:
            log.exception('não consegui apagar o arquivo sem uso: %s', nome)

    transaction.on_commit(apagar)


def _ao_apagar(sender, instance, **kwargs):
    for campo in _campos(sender):
        _apagar_depois(campo, getattr(instance, campo.name).name)


def _ao_salvar(sender, instance, raw=False, **kwargs):
    if raw or not instance.pk:
        return
    campos = _campos(sender)
    antigo = sender._default_manager.filter(pk=instance.pk).values(
        *[c.name for c in campos]).first()
    if not antigo:
        return
    for campo in campos:
        nome_antigo = antigo[campo.name]
        if nome_antigo and nome_antigo != getattr(instance, campo.name).name:
            _apagar_depois(campo, nome_antigo)


def conectar():
    for modelo in apps.get_models():
        if modelo._meta.app_label in APPS and _campos(modelo):
            models.signals.post_delete.connect(_ao_apagar, sender=modelo,
                                               dispatch_uid='arquivos-apagar-' + modelo._meta.label)
            models.signals.pre_save.connect(_ao_salvar, sender=modelo,
                                            dispatch_uid='arquivos-trocar-' + modelo._meta.label)
