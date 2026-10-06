#!/usr/bin/env bash
# Backup diário da Soar: o banco (pg_dump) e as fotos e vídeos enviados pelo
# painel. Guarda o banco no VPS e manda uma cópia de tudo para FORA dele (um
# remoto do rclone, hoje o Google Drive da Soar), porque backup que mora no
# mesmo servidor some junto com ele.
#
# Instalação (DEPLOY.md, passo 9):
#   cp deploy/backup.sh /usr/local/bin/soar-backup && chmod 750 /usr/local/bin/soar-backup
#   crontab -u soar -e   ->   15 3 * * * /usr/local/bin/soar-backup >> /var/log/soar/backup.log 2>&1
#
# Cópia fora do VPS: precisa do rclone com um remoto chamado "backup" (rclone
# config, como o usuário soar). Sem ele, o backup do banco fica só no VPS e o
# log avisa.
#
# Quanto ocupa:
#   - banco: um arquivo .sql.gz por dia, 14 dias no VPS e 60 dias no remoto;
#   - fotos e vídeos: no VPS já estão em /srv/soar/app/media (não duplica);
#     no remoto ficam espelhados e só sobe o que é novo. Nada é apagado de
#     lá: foto apagada por engano no painel continua no backup.
#
# Restaurar (teste pelo menos uma vez antes de entregar):
#   gunzip -c /srv/soar/backups/banco-AAAA-MM-DD.sql.gz | psql -h localhost -U soar -d soar_restauracao
set -euo pipefail

PASTA=/srv/soar/backups
MEDIA=/srv/soar/app/media
DIAS_VPS=14                   # retenção do banco no VPS
DIAS_REMOTO=60d               # retenção do banco no remoto
REMOTO=backup:soar-backups    # remoto do rclone : pasta
HOJE=$(date +%F)

mkdir -p "$PASTA"
umask 077                     # os arquivos de backup só o usuário soar lê

# Banco. A senha vem do ~/.pgpass do usuário soar (chmod 600), nunca da linha de comando.
pg_dump --no-owner --format=plain -h localhost -U soar soar | gzip -9 > "$PASTA/banco-$HOJE.sql.gz"

# Apaga do VPS os bancos com mais de 14 dias
find "$PASTA" -type f -name 'banco-*.sql.gz' -mtime +"$DIAS_VPS" -delete

# Cópia para fora do VPS
if command -v rclone >/dev/null && rclone listremotes | grep -q '^backup:'; then
    rclone copy "$PASTA/banco-$HOJE.sql.gz" "$REMOTO/banco/"
    rclone delete "$REMOTO/banco/" --min-age "$DIAS_REMOTO"
    if [ -d "$MEDIA" ]; then
        rclone copy "$MEDIA" "$REMOTO/media/"
    fi
    echo "$(date) backup ok: banco de $HOJE no VPS e no remoto; fotos e vídeos espelhados"
else
    echo "$(date) AVISO: rclone sem o remoto \"backup\": o banco de $HOJE ficou só no VPS" >&2
fi
