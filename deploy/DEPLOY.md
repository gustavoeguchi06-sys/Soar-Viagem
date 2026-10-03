# Deploy da Soar no VPS (Ubuntu 24.04)

Passo a passo para colocar o site no ar, na ordem. Os arquivos citados estão nesta
pasta `deploy/`. Troque `operadorasoar.com.br` pelo domínio certo, se for outro.

> Comandos com `sudo` rodam como administrador. Tudo o que é do site roda com o usuário
> `soar`, que não é administrador.

---

## 1. Servidor (checklist 7 — Segurança da VPS)

```bash
# atualiza tudo e liga as atualizações de segurança automáticas
sudo apt update && sudo apt full-upgrade -y
sudo apt install -y unattended-upgrades && sudo dpkg-reconfigure -plow unattended-upgrades

# usuário do site, sem sudo
sudo adduser --system --group --home /srv/soar soar

# firewall: só SSH, HTTP e HTTPS
sudo ufw default deny incoming && sudo ufw default allow outgoing
sudo ufw allow OpenSSH && sudo ufw allow 'Nginx Full'
sudo ufw enable
```

**SSH só por chave e sem root** (antes, confira que você já entra com a sua chave!):
em `/etc/ssh/sshd_config` deixe

```
PasswordAuthentication no
PermitRootLogin no
```

e rode `sudo systemctl restart ssh`.

**Fail2ban:** `sudo apt install -y fail2ban && sudo cp deploy/fail2ban-soar.conf /etc/fail2ban/jail.d/soar.conf && sudo systemctl restart fail2ban`

## 2. PostgreSQL (checklist 3)

```bash
sudo apt install -y postgresql
sudo -u postgres createuser --pwprompt soar      # senha forte (gerenciador de senhas)
sudo -u postgres createdb --owner soar soar
```

O PostgreSQL do Ubuntu já escuta só em `localhost` (confira `listen_addresses` em
`/etc/postgresql/*/main/postgresql.conf`). A porta 5432 **não** é aberta no firewall.

Para o backup não pedir senha: `/srv/soar/.pgpass` com
`localhost:5432:soar:soar:SENHA` e `chmod 600`.

## 3. Redis (checklist 10)

```bash
sudo apt install -y redis-server
```

Em `/etc/redis/redis.conf`: `bind 127.0.0.1 -::1` (já é o padrão) e
`requirepass UMA_SENHA_FORTE`. Depois `sudo systemctl restart redis-server`.
No `.env`: `SOAR_REDIS_URL=redis://:UMA_SENHA_FORTE@127.0.0.1:6379/0`.

## 4. O site

```bash
sudo apt install -y python3-venv nginx git
sudo -u soar git clone https://github.com/gustavoeguchi06-sys/Soar-Viagem.git /srv/soar/app
sudo -u soar python3 -m venv /srv/soar/venv
sudo -u soar /srv/soar/venv/bin/pip install -r /srv/soar/app/requirements.txt
sudo mkdir -p /var/log/soar && sudo chown soar:soar /var/log/soar
```

**`.env`** (`/srv/soar/app/.env`, `chmod 600`, dono `soar`) — modelo completo em `.env.example`:

```
SOAR_DEBUG=0
SOAR_SECRET_KEY=...            # python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
SOAR_ALLOWED_HOSTS=operadorasoar.com.br,www.operadorasoar.com.br
SOAR_ATRAS_DE_PROXY=1
SOAR_HSTS_SECONDS=3600         # subir para 31536000 depois de 1 semana com HTTPS firme
SOAR_DB_ENGINE=postgresql
SOAR_DB_PASSWORD=...
SOAR_REDIS_URL=redis://:...@127.0.0.1:6379/0
SOAR_EMAIL_BACKEND=smtp
SOAR_EMAIL_HOST=smtp.gmail.com
SOAR_EMAIL_USER=...
SOAR_EMAIL_PASSWORD=...        # senha de app do Google
SOAR_EMAIL_REMETENTE=Soar Operadora <...>
SOAR_2FA_EQUIPE=1              # recomendado: código do celular para entrar no painel
# R2 (opcional, recomendado para vídeos): SOAR_R2_BUCKET, _ACCOUNT_ID, _ACCESS_KEY, _SECRET_KEY, _DOMINIO
```

```bash
cd /srv/soar/app
sudo -u soar /srv/soar/venv/bin/python manage.py migrate
sudo -u soar /srv/soar/venv/bin/python manage.py collectstatic --noinput
sudo -u soar /srv/soar/venv/bin/python manage.py check --deploy
sudo -u soar /srv/soar/venv/bin/python manage.py criar_dono      # conta do dono (pergunta a senha)
```

**Não rode** `seed` nem `criar_exemplos_regioes` no servidor: eles criam viagens e
agência de exemplo. O dono cadastra as viagens reais pelo painel.

## 5. Gunicorn e Nginx (checklist 8)

```bash
sudo cp deploy/soar.service /etc/systemd/system/
sudo systemctl daemon-reload && sudo systemctl enable --now soar
sudo cp deploy/nginx-soar.conf /etc/nginx/sites-available/soar
sudo ln -s /etc/nginx/sites-available/soar /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo cp deploy/logrotate-soar /etc/logrotate.d/soar
```

O bloco `listen 443` só funciona depois do certificado (passo 7). Até lá, comente os
dois blocos `server { listen 443 ... }` e teste com `sudo nginx -t && sudo systemctl reload nginx`.

## 6. Domínio e DNS (checklist 19)

No painel do domínio (Registro.br ou Cloudflare):

| Tipo | Nome | Valor |
|---|---|---|
| A | `@` | IP do VPS |
| A | `www` | IP do VPS |

Confira a propagação: `dig +short operadorasoar.com.br` deve responder o IP do VPS.

> **Cloudflare com a nuvem laranja (proxy) ligada:** o IP que chega no Nginx passa a ser
> o da Cloudflare. Nesse caso, ligue o módulo `real_ip` do Nginx com as faixas de IP da
> Cloudflare (`set_real_ip_from` + `real_ip_header CF-Connecting-IP`), senão o limite de
> tentativas de login conta todos os visitantes como um só.

## 7. HTTPS (checklist 9)

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d operadorasoar.com.br -d www.operadorasoar.com.br
sudo systemctl list-timers | grep certbot      # renovação automática
sudo certbot renew --dry-run                    # testa a renovação
```

Descomente os blocos 443 do `nginx-soar.conf` (o Certbot já põe as linhas `ssl_*`) e
`sudo nginx -t && sudo systemctl reload nginx`.

## 8. Fotos e vídeos no Cloudflare R2 (checklist 4) — opcional, recomendado

1. Cloudflare → R2 → **Criar bucket** (`soar-midia`).
2. No bucket → **Configurações → Domínio personalizado**: `midia.operadorasoar.com.br`.
3. R2 → **Gerenciar tokens de API** → token com "Leitura e gravação de objetos" **só neste bucket**.
4. Preencha `SOAR_R2_BUCKET`, `SOAR_R2_ACCOUNT_ID`, `SOAR_R2_ACCESS_KEY`, `SOAR_R2_SECRET_KEY`,
   `SOAR_R2_DOMINIO` no `.env` e `sudo systemctl restart soar`.
5. Fotos que já estavam no disco: `rclone copy /srv/soar/app/media r2:soar-midia` (o caminho
   de cada arquivo continua o mesmo, então o site passa a achar tudo no R2).
6. Teste: envie uma foto pelo painel, veja no site, apague, confira que sumiu do bucket.

Não marque "acesso público via r2.dev"; o público entra só pelo domínio personalizado.

## 9. Backup (checklist 3 e 18)

```bash
sudo cp deploy/backup.sh /usr/local/bin/soar-backup && sudo chmod 750 /usr/local/bin/soar-backup
sudo chown root:soar /usr/local/bin/soar-backup
sudo apt install -y rclone && sudo -u soar rclone config      # remoto "r2backup" -> bucket de backup
sudo crontab -u soar -e     # 15 3 * * * /usr/local/bin/soar-backup >> /var/log/soar/backup.log 2>&1
```

- Retenção: 14 dias no VPS (no script) e uma regra de ciclo de vida no bucket de backup
  (ex.: apagar depois de 90 dias).
- **Teste de restauração obrigatório** antes de entregar:

```bash
sudo -u postgres createdb --owner soar soar_restauracao
gunzip -c /srv/soar/backups/banco-AAAA-MM-DD.sql.gz | psql -h localhost -U soar -d soar_restauracao
psql -h localhost -U soar -d soar_restauracao -c "select count(*) from destinations_destino;"
sudo -u postgres dropdb soar_restauracao
```

## 10. Monitoramento (checklist 17)

- **UptimeRobot** (grátis): monitor HTTPS de `https://operadorasoar.com.br/` a cada 5 min,
  alerta por e-mail/WhatsApp.
- **CPU, RAM e disco:** o painel da Hostinger mostra; para alerta, o próprio UptimeRobot ou
  `sudo apt install netdata`.
- **Logs:** Django (segurança) em `/srv/soar/app/logs/seguranca.log`; Gunicorn em
  `/var/log/soar/`; Nginx em `/var/log/nginx/soar-*.log`.
- **Erros do site por e-mail (opcional):** Sentry tem plano grátis.

## 11. Atualizar o site depois

```bash
cd /srv/soar/app && sudo -u soar git pull
sudo -u soar /srv/soar/venv/bin/pip install -r requirements.txt
sudo -u soar /srv/soar/venv/bin/python manage.py migrate
sudo -u soar /srv/soar/venv/bin/python manage.py collectstatic --noinput
sudo systemctl restart soar
```
