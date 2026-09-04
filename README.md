# ✈️ Soar Operadora — Site de Viagem

Site de viagem feito em Django: catálogo de destinos com galeria de fotos,
hospedagens com preços e avaliações de viajantes (com nota e foto).

A página de cada destino é a **página de viagem da operadora**: capa com galeria,
abas fixas, destaques, roteiro dia a dia, card de reserva com acomodações e
formas de pagamento, hospedagem, galeria, depoimentos e chamada final.
Veja em `http://127.0.0.1:8000/destinos/jalapao/` depois de rodar o `seed`.

## Como rodar (Windows)

Abra o terminal na pasta do projeto (a pasta onde está o `manage.py`) e rode
os comandos abaixo, um de cada vez:

```
python -m pip install -r requirements.txt
copy .env.example .env
python manage.py migrate
python manage.py seed
python manage.py importar_conteudo
python manage.py criar_dono
python manage.py runserver
```

O que cada um faz:

1. **install** — instala o Django e o Pillow (biblioteca de imagens).
2. **copy .env.example .env** — cria a configuração local. O `.env` que vem
   pronto liga o modo de desenvolvimento (`SOAR_DEBUG=1`). **Sem ele o projeto
   não sobe**, e isso é de propósito: o padrão de tudo aqui é o valor de
   produção, para que esquecer uma variável no servidor não deixe o site em
   modo de depuração. O `.env` nunca vai para o Git.
3. **migrate** — cria o banco de dados (arquivo `db.sqlite3`).
4. **seed** — preenche o site com destinos de exemplo (opcional, mas recomendado para ver o site funcionando).
5. **importar_conteudo** — leva para o painel os textos da página de viagem que começaram escritos no código, para você poder editá-los. Pode rodar de novo sem medo: não sobrescreve o que você já mexeu.
6. **criar_dono** — cria a conta master do dono do site. Ele pergunta a senha na hora (nada fica escrito em arquivo).
7. **runserver** — liga o servidor. **Deixe essa janela do terminal aberta** enquanto usa o site.

Depois abra no navegador:

- **Site:** http://127.0.0.1:8000/
- **Painel do dono:** http://127.0.0.1:8000/painel/ (cadastrar destinos, fotos, roteiro, hospedagens e ver as reservas)

Para parar o servidor: `Ctrl+C` no terminal.

## Uma porta de entrada, dois tipos de conta

Cliente e dono entram pela **mesma tela**: o *Entrar* do site, em
http://127.0.0.1:8000/entrar/. O painel não tem login próprio — quem digita
`/painel/` sem estar logado é mandado para lá e volta ao painel assim que
entra. Duas telas de entrada no mesmo site seria uma senha a mais para lembrar,
uma tela a mais para manter e uma a mais para um golpe copiar.

O que muda é para onde a pessoa vai depois de entrar:

| | Cliente | Dono do site |
|---|---|---|
| Como cria | botão **Entrar → Criar minha conta**, no próprio site | `python manage.py criar_dono` |
| Onde entra | http://127.0.0.1:8000/entrar/ | a mesma tela |
| Para onde vai | a página em que estava, ou a home | direto para o **painel** |
| O que faz | pede reservas e acompanha em **Minha conta** | cadastra destinos, fotos, roteiro, preços e responde as reservas |

Quem é da equipe também chega ao painel pelo menu da conta, no canto superior
direito de qualquer página do site.

**Reservar exige conta.** Quem clica em *Reservar agora* sem estar logado vai
para a tela de entrar e volta para a mesma viagem assim que entra — com a
acomodação que tinha escolhido ainda marcada. A reserva é um **pedido**: nada
é cobrado no site, a equipe confirma a vaga e combina o pagamento por fora.

Para dar acesso de dono a alguém que já tem conta de cliente:

```
python manage.py criar_dono --usuario nome.da.pessoa --promover
```

### O que dá para editar no painel

Cada destino tem, além do catálogo (nome, país, foto de capa, diária):

- **Sobre a viagem — capa:** selo, subtítulo, região e estado;
- **datas e preço:** período, mês/ano, dias, noites, próxima saída, vagas e o preço por pessoa;
- **textos:** o que está incluso e as informações importantes (um item por linha);
- **listas:** fotos da galeria, destaques da viagem, roteiro dia a dia (com foto), perguntas frequentes e hospedagens.

Tudo é opcional: o campo que ficar em branco continua usando o texto padrão da
operadora, que mora em `destinations/conteudo.py`. Ou seja, um destino novo já
nasce com a página inteira montada e você vai trocando só o que quiser.

## Colocar no ar com segurança

O padrão de toda variável é o valor **de produção**. Na sua máquina, o `.env`
(criado no passo 2) liga o modo de desenvolvimento; no servidor, você define as
variáveis de verdade e o Django **se recusa a subir** se faltar alguma das
obrigatórias.

| Variável | Para que serve |
|---|---|
| `SOAR_SECRET_KEY` | chave de assinatura. **Obrigatória.** Mínimo de 50 caracteres — chave curta é recusada |
| `SOAR_ALLOWED_HOSTS` | domínios do site, separados por vírgula. **Obrigatória** |
| `SOAR_DEBUG` | `1` só em desenvolvimento (o padrão é `0`) |
| `SOAR_SSL_REDIRECT` | `0` desliga o redirecionamento para HTTPS (padrão `1`) |
| `SOAR_HSTS_SECONDS` | validade do HSTS. Começa em `3600` de propósito |
| `SOAR_HSTS_PRELOAD` | `1` entra na lista de preload dos navegadores (só depois do HSTS em 1 ano) |
| `SOAR_ATRAS_DE_PROXY` | `1` quando um Nginx/Heroku/Render fala HTTPS no lugar do Django |
| `SOAR_CSP_SOMENTE_RELATORIO` | `0` faz a CSP bloquear de verdade (padrão: só relatar) |
| `SOAR_DB_ENGINE` | `postgresql` no servidor — veja abaixo |
| `SOAR_REDIS_URL` | onde os limites de tentativa são contados |
| `SOAR_EMAIL_BACKEND` | `smtp` para enviar confirmação e recuperação de senha de verdade |

A lista completa, comentada, está em `.env.example`.

Para gerar a chave:

```
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Com `SOAR_DEBUG=0`, entram sozinhos: redirecionamento para HTTPS, cookies de
sessão e de CSRF só por conexão segura, HSTS e `CSRF_TRUSTED_ORIGINS`.
Independente do modo já valem `X-Frame-Options: DENY` (contra clickjacking),
`nosniff`, política de referenciador `same-origin`, `Permissions-Policy`,
Content-Security-Policy e cookie de sessão fora do alcance do JavaScript.

Antes de publicar, confira com:

```
python manage.py check --deploy
```

Deve passar limpo. **Sobre o HSTS:** ele começa em 1 hora porque o navegador
guarda a instrução e não dá para cancelar antes de expirar. Confirme que o
HTTPS está firme, suba para `31536000` (um ano) e só então ligue o
`SOAR_HSTS_PRELOAD` — sair da lista de preload demora meses.

### Content-Security-Policy

Sai em modo de relatório por padrão: o navegador reclama no console mas não
bloqueia nada. Rode assim alguns dias, veja o que aparece no console, e então
mude `SOAR_CSP_SOMENTE_RELATORIO=0` para a política passar a valer.

### Banco de dados

SQLite serve para desenvolver. Em produção ele serializa as escritas — duas
reservas ao mesmo tempo viram *database is locked* — e é um arquivo único
dentro da pasta do projeto. No servidor, use Postgres:

```
SOAR_DB_ENGINE=postgresql
SOAR_DB_NAME=soar
SOAR_DB_USER=soar
SOAR_DB_PASSWORD=...
SOAR_DB_HOST=localhost
```

### Limites de tentativa

Login, cadastro, avaliação e reserva têm teto por IP e por conta. A contagem
vive no cache: sem `SOAR_REDIS_URL`, é a memória de cada processo do servidor,
então com vários workers o limite fica mais frouxo do que o configurado. Com
Redis, a contagem passa a ser de verdade.

Tentativa falha, limite estourado e entrada bem-sucedida vão para
`logs/seguranca.log` (rotação a cada 5 MB, 10 arquivos).

### Servir os arquivos enviados (Nginx)

Em desenvolvimento o próprio Django serve a pasta `media/`. Em produção quem
serve é o Nginx — e é ele que precisa mandar os cabeçalhos, porque o Django não
participa dessas requisições:

```nginx
location /media/ {
    alias /caminho/do/projeto/media/;

    # Sem isto, um arquivo enviado por um cliente pode ser interpretado como
    # HTML pelo navegador e virar XSS no mesmo domínio da sessão.
    add_header X-Content-Type-Options nosniff always;
    add_header Content-Security-Policy "default-src 'none'" always;

    # Nada de executar nada aqui dentro.
    location ~ [.](php|py|pl|cgi|sh)$ { deny all; }
}

location /static/ {
    alias /caminho/do/projeto/staticfiles/;
    expires 30d;
}
```

Melhor ainda: mande os uploads para um armazenamento externo (S3 ou
equivalente) em **outro domínio**, isolando-os do cookie de sessão.

### Envio de fotos

Avaliar exige conta. A foto passa por conferência: no máximo 2 MB, e só JPG,
PNG, WEBP ou GIF. Arquivo que não for imagem de verdade é recusado mesmo que a
extensão diga o contrário.

### O que ainda depende de infraestrutura

Duas coisas não dão para resolver só no código deste repositório:

- **Segundo fator no `/painel/`.** A conta do dono é superusuário. Instale
  `django-otp` e restrinja o caminho por IP ou VPN — só o dono precisa dele.
- **Backup do banco.** Rotina de cópia, teste de restauração e cifragem em
  repouso.

## Estrutura do projeto

```
soar/
├── manage.py            # utilitário de comandos do Django
├── requirements.txt     # dependências
├── .env.example         # modelo da configuração (copie para .env)
├── soar/                # configurações do projeto
│   ├── settings.py      # tudo por variável de ambiente; padrão = produção
│   ├── middleware.py    # Content-Security-Policy e Permissions-Policy
│   └── seguranca.py     # limites de tentativa e registro de eventos
├── destinations/        # app de destinos e hospedagens
│   ├── models.py        # Destino (com o "sobre a viagem"), DiaRoteiro, DestaqueViagem,
│   │                   # PerguntaFrequente, ImagemDestino, Hospedagem, ImagemHospedagem
│   ├── views.py         # páginas: home, lista e detalhe
│   ├── conteudo.py      # textos padrão da página de viagem, usados no que estiver em branco
│   └── management/commands/  # seed.py (exemplos) e importar_conteudo.py (código -> painel)
├── contas/              # entrar, criar conta, confirmar e-mail, sair, LGPD
│   ├── forms.py         # login por e-mail ou usuário, cadastro do cliente
│   ├── views.py         # + confirmação de e-mail, exportar e excluir os dados
│   ├── migrations/      # índice único no e-mail do usuário
│   └── management/commands/criar_dono.py  # a conta master
├── reservas/            # pedidos de reserva (exigem login)
│   ├── models.py        # Reserva (acomodação, pessoas, situação, preço do dia do pedido)
│   └── views.py         # nova reserva e cancelamento pelo cliente
├── reviews/             # app de avaliações
│   ├── models.py        # Avaliacao (nota, comentário, foto, autor, moderação)
│   └── forms.py         # formulário de avaliação (exige conta)
├── templates/           # HTML das páginas
│   ├── base.html        # cabeçalho (entrar/conta), rodapé e ícones
│   ├── contas/          # entrar, criar conta e minha conta
│   ├── reservas/nova.html  # o pedido de reserva
│   └── destinations/detalhe.html  # a página de viagem
├── static/css/          # estilo do site (style.css antigo + viagem.css + contas.css)
├── static/js/           # abas, carrosséis e acordeão do roteiro
├── static/img/          # imagens de exemplo (SVG) usadas quando não há fotos
├── media/               # fotos enviadas (criada automaticamente)
└── logs/                # registro de eventos de segurança (criada automaticamente)
```

## Como usar no dia a dia

- Cadastre destinos e hospedagens (com fotos!) pelo **painel do dono**, em `/painel/`.
- Marque um destino como **"Destaque na página inicial"** para ele aparecer no topo da home.
- As reservas chegam em **Reservas**, no painel. Mude a situação para *Confirmada* ou *Cancelada* — o cliente vê isso na tela **Minha conta**.
- **Avaliações** exigem conta e passam por você: elas chegam em *Avaliações*, no
  painel, com a situação **não publicada**. Selecione e use a ação *Publicar as
  avaliações selecionadas* para colocá-las no ar. Enquanto não publicadas, não
  aparecem no site nem contam para a nota do destino.
- Cada cliente avalia cada destino uma vez, e o nome exibido vem da conta — não
  é mais campo livre.

## Dicas

- Se aparecer erro de `Pillow`, rode: `python -m pip install Pillow`
- Se mudar os models, rode: `python manage.py makemigrations` e depois `python manage.py migrate`
- O arquivo `db.sqlite3` é o seu banco de dados — apague-o para começar do zero (e rode `migrate` + `seed` de novo).
