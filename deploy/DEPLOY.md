# Deploy da Soar no VPS (Ubuntu 26.04 LTS)

Passo a passo para colocar o site no ar, na ordem. Os arquivos citados estão nesta
pasta `deploy/` (no servidor, em `/srv/soar/app/deploy/`). Troque `operadorasoar.com.br`
pelo domínio certo, se for outro.

> Comandos com `sudo` rodam como administrador. Tudo o que é do site roda com o usuário
> `soar`, que não é administrador.

**O que o Ubuntu 26.04 traz e o site já aceita:** Python 3.14 (o mesmo usado no
desenvolvimento; todas as bibliotecas do `requirements.txt` têm versão pronta para ele, nada
é compilado), PostgreSQL 18 e Nginx com `http2 on`. O `sudo` do 26.04 é o sudo-rs: os
comandos são os mesmos.

---

## 0. Primeiro acesso e usuário administrador

A Hostinger entrega a VPS com o usuário `root`. Do seu computador (PowerShell):

```bash
ssh root@IP_DO_VPS
```

Crie o seu usuário de administrador (troque `SEU_USUARIO`, ex.: `gustavo`) e passe para
ele a chave SSH que o `root` já tem:

```bash
adduser SEU_USUARIO
usermod -aG sudo SEU_USUARIO
mkdir -p /home/SEU_USUARIO/.ssh
cp /root/.ssh/authorized_keys /home/SEU_USUARIO/.ssh/
chown -R SEU_USUARIO:SEU_USUARIO /home/SEU_USUARIO/.ssh
chmod 700 /home/SEU_USUARIO/.ssh && chmod 600 /home/SEU_USUARIO/.ssh/authorized_keys
```

> Se a chave não foi cadastrada na Hostinger (o `cp` reclama que o arquivo não existe),
> mande ela do seu computador, no PowerShell:
> `type $env:USERPROFILE\.ssh\id_ed25519.pub | ssh SEU_USUARIO@IP_DO_VPS "mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys && chmod 700 ~/.ssh && chmod 600 ~/.ssh/authorized_keys"`

**Abra outro PowerShell** e confira que entra sem senha e que o `sudo` funciona:
`ssh SEU_USUARIO@IP_DO_VPS` e depois `sudo -v`. A partir daqui, use sempre esse usuário.

## 1. Servidor (checklist 7 — Segurança da VPS)

```bash
# atualiza tudo e liga as atualizações de segurança automáticas
sudo apt update && sudo apt full-upgrade -y
sudo apt install -y unattended-upgrades ufw git && sudo dpkg-reconfigure -plow unattended-upgrades

# usuário do site, sem sudo
sudo adduser --system --group --home /srv/soar soar

# firewall: só SSH, HTTP e HTTPS (por porta: o perfil "Nginx Full" só existe
# depois de instalar o Nginx)
sudo ufw default deny incoming && sudo ufw default allow outgoing
sudo ufw allow OpenSSH && sudo ufw allow 80,443/tcp
sudo ufw enable
```

**SSH só por chave e sem root.** No Ubuntu 26.04 a configuração vale pelo **primeiro**
arquivo que define cada opção, e a imagem da VPS costuma trazer um
`/etc/ssh/sshd_config.d/50-cloud-init.conf` ligando a senha. Por isso o nosso arquivo leva
o nome `00-`, para ser lido antes:

```bash
printf 'PasswordAuthentication no\nKbdInteractiveAuthentication no\nPermitRootLogin no\n' \
  | sudo tee /etc/ssh/sshd_config.d/00-soar.conf
sudo sshd -t && sudo systemctl reload ssh
sudo sshd -T | grep -Ei '^(passwordauthentication|permitrootlogin)'   # deve dizer "no" nos dois
```

**Antes de fechar a sessão**, confira num PowerShell novo que `ssh SEU_USUARIO@IP_DO_VPS`
ainda entra. (Se trancar do lado de fora, o painel da Hostinger tem um terminal de
emergência.)

O **Fail2ban** entra no fim do passo 7, porque ele lê o log do Nginx.

## 2. PostgreSQL (checklist 3)

```bash
sudo apt install -y postgresql            # no 26.04: PostgreSQL 18
sudo -u postgres createuser --pwprompt soar      # senha forte (gerenciador de senhas)
sudo -u postgres createdb --owner soar soar
```

O PostgreSQL do Ubuntu já escuta só em `localhost` (confira `listen_addresses` em
`/etc/postgresql/18/main/postgresql.conf`). A porta 5432 **não** é aberta no firewall.

Para o backup não pedir senha (troque `SENHA` pela do banco):

```bash
echo 'localhost:5432:soar:soar:SENHA' | sudo -u soar tee /srv/soar/.pgpass >/dev/null
sudo chmod 600 /srv/soar/.pgpass
```

## 3. Redis (checklist 10)

```bash
sudo apt install -y redis-server
```

> Se o Ubuntu disser que `redis-server` não existe, instale o **Valkey**, que é o mesmo
> Redis com outro nome (o site fala com ele do mesmo jeito):
> `sudo apt install -y valkey-server`. Aí o arquivo de configuração é
> `/etc/valkey/valkey.conf` e o serviço é `valkey-server`.

No arquivo de configuração (`/etc/redis/redis.conf`): `bind 127.0.0.1 -::1` (já é o
padrão) e `requirepass UMA_SENHA_FORTE`. Depois `sudo systemctl restart redis-server`
(ou `valkey-server`). No `.env`: `SOAR_REDIS_URL=redis://:UMA_SENHA_FORTE@127.0.0.1:6379/0`.

## 4. O site

```bash
sudo apt install -y python3-venv nginx
sudo -u soar git clone https://github.com/gustavoeguchi06-sys/Soar-Viagem.git /srv/soar/app
sudo -u soar python3 -m venv /srv/soar/venv
sudo -u soar /srv/soar/venv/bin/pip install -r /srv/soar/app/requirements.txt
sudo -u soar mkdir -p /srv/soar/app/media /srv/soar/app/logs
sudo mkdir -p /var/log/soar && sudo chown soar:soar /var/log/soar
```

**`.env`** (`/srv/soar/app/.env`, só o usuário `soar` lê). Parta do modelo completo:

```bash
sudo -u soar cp /srv/soar/app/.env.example /srv/soar/app/.env
sudo chmod 600 /srv/soar/app/.env
sudo nano /srv/soar/app/.env
```

Preencha pelo menos estas linhas. **Comentário só em linha própria**, começando com `#`:
um `# ...` depois do valor vira parte do valor e o site não sobe.

```
SOAR_DEBUG=0
# gere com: /srv/soar/venv/bin/python -c "import secrets; print(secrets.token_urlsafe(64))"
SOAR_SECRET_KEY=...
SOAR_ALLOWED_HOSTS=operadorasoar.com.br,www.operadorasoar.com.br
SOAR_ATRAS_DE_PROXY=1
# subir para 31536000 depois de 1 semana com HTTPS firme
SOAR_HSTS_SECONDS=3600
SOAR_DB_ENGINE=postgresql
SOAR_DB_PASSWORD=...
SOAR_REDIS_URL=redis://:...@127.0.0.1:6379/0
SOAR_EMAIL_BACKEND=smtp
SOAR_EMAIL_HOST=smtp.gmail.com
SOAR_EMAIL_USER=...
# senha de app do Google
SOAR_EMAIL_PASSWORD=...
SOAR_EMAIL_REMETENTE=Soar Operadora <...>
# recomendado: código do celular para entrar no painel
SOAR_2FA_EQUIPE=1
# fotos do @operadorasoar na página inicial: copie a linha do .env do seu computador
SOAR_INSTAGRAM_TOKEN=...
# R2 (opcional, recomendado para vídeos): SOAR_R2_BUCKET, _ACCOUNT_ID, _ACCESS_KEY, _SECRET_KEY, _DOMINIO
```

```bash
cd /srv/soar/app
sudo -u soar /srv/soar/venv/bin/python manage.py migrate
sudo -u soar /srv/soar/venv/bin/python manage.py collectstatic --noinput
sudo -u soar /srv/soar/venv/bin/python manage.py check --deploy
sudo -u soar /srv/soar/venv/bin/python manage.py criar_dono      # conta do dono (pergunta a senha)
```

O `check --deploy` deve mostrar só o aviso `security.W021` (HSTS preload), que é de
propósito: ele só liga depois do HSTS estar em um ano.

**Não rode** `seed` nem `criar_exemplos_regioes` no servidor: eles criam viagens e
agência de exemplo. O dono cadastra as viagens reais pelo painel.

## 5. Gunicorn (checklist 8)

```bash
sudo cp /srv/soar/app/deploy/soar.service /etc/systemd/system/
sudo systemctl daemon-reload && sudo systemctl enable --now soar
sudo systemctl status soar                       # deve estar "active (running)"
curl -sI http://127.0.0.1:8000/ | head -1        # o site responde por dentro do servidor
sudo cp /srv/soar/app/deploy/logrotate-soar /etc/logrotate.d/soar
```

O Nginx (a porta de entrada da internet) é configurado no passo 7, depois do certificado:
a configuração dele já aponta para o certificado, então ele só sobe com o certificado
emitido.

## 6. Domínio e DNS (checklist 19)

No painel do domínio (Registro.br ou Cloudflare):

| Tipo | Nome | Valor |
|---|---|---|
| A | `@` | IP do VPS |
| A | `www` | IP do VPS |

**Ao trocar, o site do Wix sai do ar**: escolha um horário de pouco movimento.
Confira a propagação: `dig +short operadorasoar.com.br` e `dig +short www.operadorasoar.com.br`
devem responder o IP do VPS. Só siga para o passo 7 depois disso.

> **Cloudflare com a nuvem laranja (proxy) ligada:** o IP que chega no Nginx passa a ser
> o da Cloudflare. Nesse caso, ligue o módulo `real_ip` do Nginx com as faixas de IP da
> Cloudflare (`set_real_ip_from` + `real_ip_header CF-Connecting-IP`), senão o limite de
> tentativas de login conta todos os visitantes como um só. Deixe a nuvem **cinza** durante
> o passo 7.

## 7. HTTPS e Nginx (checklist 8 e 9)

O certificado sai primeiro, com o Certbot no modo "standalone" (ele mesmo atende a
conferência da Let's Encrypt na porta 80, com o Nginx parado por alguns segundos):

```bash
sudo apt install -y certbot
sudo certbot certonly --standalone \
  -d operadorasoar.com.br -d www.operadorasoar.com.br \
  --pre-hook "systemctl stop nginx" --post-hook "systemctl start nginx"
```

Os dois ganchos ficam gravados: a cada renovação automática (a cada ~60 dias) o Nginx para
por alguns segundos e volta sozinho.

Agora a configuração do site no Nginx (ela já aponta para o certificado emitido acima):

```bash
sudo cp /srv/soar/app/deploy/nginx-soar.conf /etc/nginx/sites-available/soar
sudo ln -s /etc/nginx/sites-available/soar /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl reload nginx
```

Confira:

```bash
curl -sI http://operadorasoar.com.br/ | head -3        # 301 para https://
curl -sI https://www.operadorasoar.com.br/ | head -3   # 301 para https://operadorasoar.com.br/
curl -sI https://operadorasoar.com.br/ | head -1       # 200
sudo systemctl list-timers | grep certbot              # renovação automática agendada
sudo certbot renew --dry-run                           # testa a renovação
```

**Fail2ban** (agora que o log do Nginx existe):

```bash
sudo apt install -y fail2ban python3-systemd
sudo cp /srv/soar/app/deploy/fail2ban-soar.conf /etc/fail2ban/jail.d/soar.conf
sudo systemctl restart fail2ban
sudo fail2ban-client status        # deve listar sshd e nginx-limit-req
```

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
sudo cp /srv/soar/app/deploy/backup.sh /usr/local/bin/soar-backup
sudo chown root:soar /usr/local/bin/soar-backup && sudo chmod 750 /usr/local/bin/soar-backup
sudo apt install -y rclone && sudo -u soar rclone config      # remoto "r2backup" -> bucket de backup
sudo -u soar /usr/local/bin/soar-backup                       # roda uma vez à mão para conferir
sudo crontab -u soar -e     # 15 3 * * * /usr/local/bin/soar-backup >> /var/log/soar/backup.log 2>&1
```

- Retenção: 14 dias no VPS (no script) e uma regra de ciclo de vida no bucket de backup
  (ex.: apagar depois de 90 dias).
- **Teste de restauração obrigatório** antes de entregar:

```bash
sudo -u postgres createdb --owner soar soar_restauracao
gunzip -c /srv/soar/backups/banco-AAAA-MM-DD.sql.gz | sudo -u soar psql -h localhost -U soar -d soar_restauracao
sudo -u soar psql -h localhost -U soar -d soar_restauracao -c "select count(*) from destinations_destino;"
sudo -u postgres dropdb soar_restauracao
```

### Fotos do Instagram (@operadorasoar)

A linha `SOAR_INSTAGRAM_TOKEN=` já entrou no `.env` no passo 4. O token vence em 60 dias; o
site renova sozinho a cada 7 dias quando busca as fotos, e o cron abaixo garante a
renovação mesmo numa semana sem visitas:

```bash
sudo crontab -u soar -e     # 30 4 * * * cd /srv/soar/app && /srv/soar/venv/bin/python manage.py renovar_token_instagram >> /var/log/soar/instagram.log 2>&1
```

Se o token vencer ou for revogado, gere outro no painel da Meta e troque no `.env`; o novo
passa na frente do que estava guardado no banco.

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

Se o arquivo de algum serviço mudou (`deploy/soar.service`, `deploy/nginx-soar.conf`,
`deploy/fail2ban-soar.conf`), copie de novo para o lugar dele, como nos passos 5 e 7.
