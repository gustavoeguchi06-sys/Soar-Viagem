#!/usr/bin/env bash
# Backup diário da Soar: banco (pg_dump) e, se as fotos estiverem no disco, a
# pasta media. Guarda no VPS e manda uma cópia para FORA dele (bucket R2 de
# backup), porque backup que mora no mesmo servidor some junto com ele.
#
# Instalação (como root):
#   cp deploy/backup.sh /usr/local/bin/soar-backup && chmod 750 /usr/local/bin/soar-backup
#   crontab -u soar -e   ->   15 3 * * * /usr/local/bin/soar-backup >> /var/log/soar/backup.log 2>&1
#
# Precisa do rclone configurado com um remoto chamado "r2backup" apontando para
# um bucket SÓ de backup (rclone config; tipo S3, provedor Cloudflare).
# Restaurar (teste pelo menos uma vez antes de entregar):
#   gunzip -c /srv/soar/backups/banco-AAAA-MM-DD.sql.gz | psql -U soar -d soar_restauracao
set -euo pipefail

PASTA=/srv/soar/backups
DIAS=14                       # retenção no VPS
REMOTO=r2backup:soar-backups  # retenção no R2: regra de ciclo de vida do bucket (ex.: 90 dias)
HOJE=$(date +%F)

mkdir -p "$PASTA"
umask 077                     # os arquivos de backup só o usuário soar lê

# Banco. A senha vem do ~/.pgpass do usuário soar (chmod 600), nunca da linha de comando.
pg_dump --no-owner --format=plain -h localhost -U soar soar | gzip -9 > "$PASTA/banco-$HOJE.sql.gz"

# Fotos e vídeos: só se estiverem no disco (sem R2). Com R2, o próprio bucket guarda.
if [ -d /srv/soar/app/media ] && [ -n "$(ls -A /srv/soar/app/media 2>/dev/null)" ]; then
    tar -czf "$PASTA/media-$HOJE.tar.gz" -C /srv/soar/app media
fi

# Cópia para fora do VPS
if command -v rclone >/dev/null && rclone listremotes | grep -q '^r2backup:'; then
    rclone copy "$PASTA" "$REMOTO" --include "*-$HOJE.*"
else
    echo "$(date) AVISO: rclone/r2backup não configurado, backup ficou só no VPS" >&2
fi

# Apaga os antigos do VPS
find "$PASTA" -type f -mtime +"$DIAS" -delete

echo "$(date) backup ok: $(ls -1 "$PASTA" | grep -c "$HOJE") arquivo(s) de $HOJE"
