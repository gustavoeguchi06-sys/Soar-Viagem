# ✈️ Soar Operadora — Site de viagens em grupo (B2B)

Site da operadora Soar, feito em Django. A Soar é **B2B**: o público vê as
viagens, as datas e os preços, mas **não compra pelo site**. Quem vende são as
**agências parceiras**, que fazem o orçamento na própria página da viagem e
mandam para o cliente delas em PDF, por e-mail.

| Quem | O que faz no site |
|---|---|
| **Visitante** | Vê viagens, roteiro, preços por quarto, datas e quartos disponíveis, blog, Soar 60+ e "Sobre a Soar". Pede **"Saiba mais"** e deixa o contato. |
| **Agência parceira** | Se cadastra (área **B2B**, com CNPJ e CADASTUR). Depois de aprovada, faz **orçamentos** no card da viagem: o PDF vai para o e-mail do cliente e vale 72 horas. |
| **Equipe / dono** | No **painel** (`/painel/`): viagens, preços, datas, fotos e vídeos, banner da página inicial, página "Sobre", blog, avaliações, agências, orçamentos e os interessados do "Saiba mais". |

Guias para o cliente (PDF, fora do repositório): **Guia do painel do dono** e
**Guia de fotos e vídeos**.

## Como rodar na sua máquina (Windows)

Na pasta do `manage.py`:

```
python -m pip install -r requirements.txt
copy .env.example .env
python manage.py migrate
python manage.py seed
python manage.py importar_conteudo
python manage.py criar_dono
python manage.py runserver
```

1. **install** — instala as dependências (versões fixadas no `requirements.txt`).
2. **copy .env.example .env** — o `.env` que vem pronto liga o modo de
   desenvolvimento (`SOAR_DEBUG=1`). **Sem ele o projeto não sobe**, de propósito:
   o padrão de tudo é o valor de produção. O `.env` nunca vai para o Git.
3. **migrate** — cria o banco (`db.sqlite3`).
4. **seed** — viagens, hospedagens e avaliações **de exemplo**, para ver o site
   funcionando. `criar_exemplos_regioes` acrescenta uma viagem por região.
   **Não rode nenhum dos dois no servidor.**
5. **importar_conteudo** — leva para o painel os textos padrão da página de
   viagem, para serem editados. Não sobrescreve o que já foi mexido.
6. **criar_dono** — cria a conta do dono (pergunta a senha na hora).
7. **runserver** — liga o site. Ou dê dois cliques no **`rodar.bat`**, que faz o
   migrate, apaga dados vencidos (LGPD) e abre o navegador.

- Site: http://127.0.0.1:8000/
- Painel: http://127.0.0.1:8000/painel/

## Uma tela de entrada para todos

Agência e equipe entram pela mesma tela, `/entrar/`. O painel não tem login
próprio: quem abre `/painel/` sem estar logado vai para lá e volta ao painel.

| | Agência parceira | Equipe / dono |
|---|---|---|
| Como cria a conta | **B2B → Cadastrar minha agência**; o dono aprova no painel | `python manage.py criar_dono` (ou `--usuario nome --promover`) |
| Depois de entrar | painel da agência (visão geral e dados) | painel do dono |
| Código do celular | — | opcional, `SOAR_2FA_EQUIPE=1` (recomendado em produção) |

Conta antiga de cliente (de quando o site vendia direto) é recusada ao entrar.

## O que o dono edita no painel

- **Destinos:** catálogo, **preço por pessoa de cada quarto** (Single, Casal,
  Duplo, Triplo — o "a partir de" é o menor), **datas de saída com os quartos
  disponíveis de cada tipo**, faixa de serviços (com seletor de ícones), roteiro
  dia a dia, destaques, incluso/não incluso, informações, perguntas frequentes,
  hospedagem, fotos e **vídeos** da galeria. O que ficar em branco usa o texto
  padrão de `destinations/conteudo.py`; fotos aparecem só as cadastradas.
- **Página inicial:** fotos e vídeos do banner (vídeo toca sem som, em repetição).
- **Sobre a Soar:** capa com foto ou vídeo, texto, diferenciais, números e fotos.
- **Soar 60+:** vídeos da página do programa.
- **Blog:** artigos em seções (com foto e vídeo), rascunho/agendado/no ar, e a
  lista de e-mails da newsletter.
- **Avaliações:** o dono cadastra e publica.
- **Agências, orçamentos e interessados** (o "Saiba mais"; só o dono vê).

## Orçamento da agência

No card da viagem, a agência escolhe data, quarto, adultos e as idades das
crianças (CHD, 0 a 8 anos, sob consulta). O pop-up pede o responsável e o
e-mail; o site calcula o valor pela tabela (preço do quarto × adultos), guarda o
orçamento com validade de **72 horas** e manda o **PDF** com o pacote completo:
foto de capa, formas de pagamento logo abaixo do valor, roteiro, as fotos dos
lugares que o grupo vai conhecer, incluso e não incluso, hospedagem com foto e
informações importantes. Se o e-mail falhar, o
orçamento fica salvo e a agência baixa o PDF. Limite: 30 orçamentos por hora por
agência (`SOAR_LIMITE_ORCAMENTO`).

## Colocar no ar

**Passo a passo completo do servidor em [`deploy/DEPLOY.md`](deploy/DEPLOY.md)**
(Ubuntu 26.04 + Nginx + Gunicorn + PostgreSQL + Redis + Certbot, com firewall, SSH,
Fail2ban, backup e monitoramento). Os arquivos de configuração estão em `deploy/`.

O padrão de toda variável é o de **produção**, e o Django **se recusa a subir**
se faltar uma obrigatória. Principais (lista completa e comentada em
`.env.example`):

| Variável | Para que serve |
|---|---|
| `SOAR_SECRET_KEY` | **obrigatória**; mínimo 50 caracteres, chave fraca é recusada |
| `SOAR_ALLOWED_HOSTS` | **obrigatória**; domínios separados por vírgula (gera o `CSRF_TRUSTED_ORIGINS`) |
| `SOAR_DEBUG` | `1` só em desenvolvimento |
| `SOAR_ATRAS_DE_PROXY` | `1` atrás do Nginx (HTTPS e IP real do visitante) |
| `SOAR_HSTS_SECONDS` | começa em `3600`; suba para `31536000` com o HTTPS firme |
| `SOAR_DB_ENGINE` | `postgresql` no servidor (+ `SOAR_DB_*`) |
| `SOAR_REDIS_URL` | onde os limites de tentativa são contados |
| `SOAR_EMAIL_*` | SMTP (Gmail com senha de app): orçamentos, nova senha, confirmação |
| `SOAR_R2_*` | fotos e vídeos no **Cloudflare R2** em vez do disco do VPS (opcional) |
| `SOAR_2FA_EQUIPE` | `1` pede código do celular para entrar no painel |
| `SOAR_INSTAGRAM_TOKEN` | fotos do @operadorasoar na página inicial (renovado sozinho) |
| `SOAR_TAMANHO_MAXIMO_*_MB` | teto de envio (10), de cada foto (10) e de cada vídeo (100) |

Antes de publicar: `python manage.py check --deploy` (o único aviso esperado é o
do HSTS preload, desligado de propósito).

## Segurança (o que já está no código)

- **Cabeçalhos:** em produção, HTTPS obrigatório, HSTS e cookies só por conexão
  segura. Sempre: CSP bloqueando (sem script de fora nem inline), `X-Frame-Options:
  DENY`, `nosniff`, `Referrer-Policy` e `Permissions-Policy`.
- **Limites de tentativa** por IP e por conta: login (5 em 15 min), cadastro de
  agência, nova senha, newsletter, "Saiba mais", orçamento e código do celular.
  Atrás do Nginx, o IP vem do cabeçalho que o **nosso** proxy escreve (o
  visitante não consegue forjar).
- **Uploads:** só no painel e só pela equipe. Fotos JPG/PNG/WebP/GIF até 10 MB,
  conferidas pelo conteúdo; vídeos MP4/WebM até 100 MB, conferidos pelo
  cabeçalho do arquivo. O teto maior de envio vale só para a equipe em `/painel/`.
  Arquivo trocado ou apagado sai do disco/R2 (`soar/arquivos.py`).
- **Permissões:** agência só vê e baixa o que é dela; interessados e usuários só
  o dono. Há uma varredura automática das áreas protegidas (`contas/tests/test_permissoes.py`).
- **LGPD:** aviso de privacidade, exportar e excluir os próprios dados, e o
  comando `expurgar_dados`, que apaga o que passou do prazo (agende uma vez por
  dia no servidor; o `rodar.bat` já roda local).
- **Logs:** eventos de segurança em `logs/seguranca.log`, um arquivo por dia,
  183 dias (Marco Civil). Nunca guardam senha, token ou código.

## Testes

```
python manage.py test
```

Cada correção de segurança e cada regra de negócio tem teste que quebra se
alguém desfizer (permissões, limites, uploads, preços, orçamento e PDF, e-mail,
Instagram, N+1 nas listas). Os testes de cada módulo ficam em `<módulo>/tests/`,
um arquivo por assunto (`test_precos.py`, `test_permissoes.py`...).

## Arquitetura

Um projeto Django com um módulo (app) por assunto do negócio. Cada módulo tem as
mesmas camadas, e cada camada tem um papel só:

| Camada | Arquivo | O que faz |
|---|---|---|
| Dados | `models.py` | tabelas e regras que valem sempre (validações, cálculos do próprio registro) |
| Regras de negócio | módulos com nome do assunto: `conteudo.py`, `inicio.py`, `instagram.py`, `pdf.py`... | montam o que as telas mostram; não sabem nada de HTTP |
| Telas | `views.py` + `urls.py` + `templates/<módulo>/` | recebem o pedido, chamam as regras e devolvem a página |
| Formulários | `forms.py` | o que o visitante digita e a conferência disso |
| Painel do dono | `admin.py` | como cada cadastro aparece e quem pode ver e mexer |
| Rotinas | `management/commands/` | comandos agendados ou de manutenção (`expurgar_dados`, `renovar_token_instagram`...) |
| Testes | `tests/test_<assunto>.py` | um arquivo por assunto |

O que é de todos os módulos (segurança, CSP, validação de arquivos, o painel)
fica no núcleo, `soar/`.

```
soar/                    # raiz do projeto (onde está o manage.py)
├── manage.py · requirements.txt · .env.example · rodar.bat
├── deploy/              # servidor: DEPLOY.md, nginx, gunicorn, systemd, backup, fail2ban, logrotate
├── soar/                # núcleo e configurações
│   ├── settings.py      # tudo por variável de ambiente; padrão = produção
│   ├── urls.py          # as rotas de cada módulo, juntas
│   ├── middleware.py    # CSP, Permissions-Policy e teto de envio
│   ├── seguranca.py     # limites de tentativa e IP do visitante
│   ├── painel.py        # o painel do dono (abas e tela inicial)
│   ├── videos.py        # validação de fotos e vídeos enviados
│   ├── arquivos.py      # apaga arquivo que ficou sem uso
│   ├── mascaras.py      # telefone, CEP, CADASTUR no formato brasileiro
│   └── limpeza_sw.py    # /sw.js e /favicon.ico
├── destinations/        # viagens: destino, preços por quarto, saídas, roteiro, fotos, vídeos,
│   │                    # serviços, banner, Soar 60+, Sobre a Soar, "Saiba mais", Instagram
│   ├── conteudo.py      # monta a página da viagem (o que está no painel ou o texto padrão)
│   ├── inicio.py        # monta a página inicial
│   ├── instagram.py     # fotos do @operadorasoar e renovação do token
│   └── quartos.py       # tipos de quarto e ícones
├── agencia/             # orçamento no card da viagem, PDF (pdf.py) e e-mail
├── contas/              # entrar, B2B (cadastro da agência), 2FA, Google, senha, LGPD
├── blog/                # artigos, categorias e newsletter
├── reviews/             # avaliações (cadastradas pelo dono)
├── templates/           # HTML, numa pasta por módulo (+ base.html, páginas de erro, painel)
├── static/              # css/ (um por área), js/, fonts/, img/
├── media/               # fotos e vídeos enviados (sem R2; fora do Git)
└── logs/                # log de segurança (fora do Git)
```

O nome `destinations` (em inglês, ao contrário dos outros) fica: ele está gravado
nas tabelas do banco e nas migrações, e trocar não vale o risco.

## Dicas

- Mudou um model: `python manage.py makemigrations` e `python manage.py migrate`.
- Começar do zero (só na sua máquina): apague `db.sqlite3` e rode `migrate` + `seed`.
- E-mail local sem SMTP: as mensagens aparecem no terminal do `runserver`.
