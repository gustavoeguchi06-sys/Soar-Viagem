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
python manage.py migrate
python manage.py seed
python manage.py createsuperuser
python manage.py runserver
```

O que cada um faz:

1. **install** — instala o Django e o Pillow (biblioteca de imagens).
2. **migrate** — cria o banco de dados (arquivo `db.sqlite3`).
3. **seed** — preenche o site com 5 destinos de exemplo (opcional, mas recomendado para ver o site funcionando).
4. **createsuperuser** — cria seu usuário de administrador (escolha nome e senha).
5. **runserver** — liga o servidor. **Deixe essa janela do terminal aberta** enquanto usa o site.

Depois abra no navegador:

- **Site:** http://127.0.0.1:8000/
- **Admin:** http://127.0.0.1:8000/admin/ (para cadastrar destinos, fotos, hospedagens...)

Para parar o servidor: `Ctrl+C` no terminal.

## Colocar no ar com segurança

Rodando na sua máquina não precisa configurar nada: o projeto já sobe com
`DEBUG` ligado e só aceita `localhost`. Para publicar, defina estas variáveis
de ambiente — o Django **se recusa a subir** sem as duas primeiras:

| Variável | Para que serve |
|---|---|
| `SOAR_SECRET_KEY` | chave de assinatura. **Obrigatória.** A chave de exemplo está no repositório, então serve só para desenvolvimento |
| `SOAR_ALLOWED_HOSTS` | domínios do site, separados por vírgula. **Obrigatória** |
| `SOAR_DEBUG` | `0` no servidor (o padrão é `1`) |
| `SOAR_SSL_REDIRECT` | `0` desliga o redirecionamento para HTTPS (padrão `1`) |
| `SOAR_HSTS_SECONDS` | validade do HSTS. Começa em `3600` de propósito |
| `SOAR_ATRAS_DE_PROXY` | `1` quando um Nginx/Heroku/Render fala HTTPS no lugar do Django |

Para gerar a chave:

```
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Com `SOAR_DEBUG=0`, entram sozinhos: redirecionamento para HTTPS, cookies de
sessão e de CSRF só por conexão segura, HSTS e `CSRF_TRUSTED_ORIGINS`.
Independente do modo já valem `X-Frame-Options: DENY` (contra clickjacking),
`nosniff`, política de referenciador `same-origin` e cookie de sessão fora do
alcance do JavaScript.

Antes de publicar, confira com:

```
python manage.py check --deploy
```

O único aviso esperado é o `security.W021` (HSTS preload): entrar na lista de
preload dos navegadores é praticamente irreversível, então fica desligado até
você decidir.

**Sobre o HSTS:** ele começa em 1 hora porque o navegador guarda a instrução e
não dá para cancelar antes de expirar. Confirme que o HTTPS está firme e só
então suba para `31536000` (um ano).

### Envio de fotos

O formulário de avaliação é público, então a foto passa por conferência: no
máximo 5 MB, e só JPG, PNG, WEBP ou GIF. Arquivo que não for imagem de verdade
é recusado mesmo que a extensão diga o contrário.

## Estrutura do projeto

```
soar/
├── manage.py            # utilitário de comandos do Django
├── requirements.txt     # dependências
├── soar/                # configurações do projeto (settings, urls)
├── destinations/        # app de destinos e hospedagens
│   ├── models.py        # Destino, ImagemDestino, Hospedagem, ImagemHospedagem
│   ├── views.py         # páginas: home, lista e detalhe
│   ├── conteudo.py      # textos da página de viagem (roteiro, FAQ, acomodações...)
│   └── management/commands/seed.py  # dados de exemplo
├── reviews/             # app de avaliações
│   ├── models.py        # Avaliacao (nota, comentário, foto)
│   └── forms.py         # formulário público de avaliação
├── templates/           # HTML das páginas
│   ├── base.html        # cabeçalho, rodapé e ícones
│   └── destinations/detalhe.html  # a página de viagem
├── static/css/          # estilo do site (style.css antigo + viagem.css)
├── static/js/           # abas, carrosséis e acordeão do roteiro
├── static/img/          # imagens de exemplo (SVG) usadas quando não há fotos
└── media/               # fotos enviadas (criada automaticamente)
```

## Como usar no dia a dia

- Cadastre destinos e hospedagens (com fotos!) pelo **admin**.
- Marque um destino como **"Destaque na página inicial"** para ele aparecer no topo da home.
- Visitantes podem deixar **avaliações** direto na página de cada destino, sem precisar de login.

## Dicas

- Se aparecer erro de `Pillow`, rode: `python -m pip install Pillow`
- Se mudar os models, rode: `python manage.py makemigrations` e depois `python manage.py migrate`
- O arquivo `db.sqlite3` é o seu banco de dados — apague-o para começar do zero (e rode `migrate` + `seed` de novo).
