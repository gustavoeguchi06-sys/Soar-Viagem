"""
Comando para popular o banco com dados de exemplo.
Uso: python manage.py seed
"""
from django.core.management.base import BaseCommand
from django.utils.text import slugify

from destinations.models import Destino, Hospedagem
from reviews.models import Avaliacao


class Command(BaseCommand):
    help = 'Cria destinos, hospedagens e avaliações de exemplo'

    def handle(self, *args, **options):
        dados = [
            {
                'nome': 'Alter do Chão', 'slug': 'alter-do-chao', 'pais': 'Brasil', 'regiao': 'Norte',
                'descricao': 'O Caribe amazônico: praias de areia branca que surgem na seca do rio '
                             'Tapajós, água doce e transparente, a famosa Ilha do Amor e o pôr do sol '
                             'mais bonito do Pará. A vila reúne floresta, cultura ribeirinha e um '
                             'ritmo tranquilo a 30 km de Santarém.',
                'preco_base': 3576, 'melhor_epoca': 'Agosto a janeiro (seca do Tapajós)',
                'destaque': True,
                'hospedagens': [
                    ('Pousada Vila Amazônia', 'pousada', 420, 'A duas quadras da Ilha do Amor, com '
                                                              'piscina, rede na varanda e café da manhã regional.'),
                    ('Hotel Beira Tapajós', 'hotel', 560, 'Quartos com vista para o rio e '
                                                          'deck próprio para o pôr do sol.'),
                ],
                'avaliacoes': [
                    ('Mariana S.', 5, 'Lugar incrível! A Soar cuidou de tudo nos mínimos detalhes.'),
                    ('Bruno C.', 5, 'A Ilha do Amor no fim da tarde é uma das coisas mais bonitas '
                                    'que já vi no Brasil.'),
                    ('Letícia A.', 5, 'Passeio de voadeira no Lago Verde valeu cada centavo. '
                                      'Guia local excelente!'),
                ],
            },
            {
                'nome': 'Jalapão/TO', 'slug': 'jalapao', 'pais': 'Brasil', 'regiao': 'Norte',
                'descricao': 'Uma aventura no coração do Brasil: fervedouros de água cristalina onde é '
                             'impossível afundar, dunas alaranjadas com o pôr do sol mais bonito do '
                             'cerrado, cânions, cachoeiras e o artesanato de capim dourado.',
                'preco_base': 3588, 'melhor_epoca': 'Maio a setembro', 'destaque': True,
                'hospedagens': [
                    ('Pousada Jalapão', 'pousada', 480, 'Conforto e natureza, com piscina, '
                                                        'ar-condicionado e café da manhã regional.'),
                ],
                'avaliacoes': [
                    ('Mariana S.', 5, 'Foi sem dúvidas a maior aventura que já fiz. Tudo muito bem '
                                      'organizado e os guias são incríveis!'),
                    ('Ricardo T.', 5, 'O Jalapão com a Soar superou minhas expectativas. Cada detalhe '
                                      'feito com muito carinho.'),
                    ('Ana Paula L.', 5, 'A energia do grupo e os lugares incríveis tornam a viagem '
                                        'inesquecível. Já quero a próxima!'),
                ],
            },
            {
                'nome': 'Fernando de Noronha', 'pais': 'Brasil', 'regiao': 'Nordeste',
                'descricao': 'Arquipélago paradisíaco com as praias mais bonitas do Brasil. '
                             'Águas cristalinas, mergulho com tartarugas e golfinhos, e o famoso '
                             'pôr do sol do Forte do Boldró.',
                'preco_base': 3900, 'melhor_epoca': 'Agosto a dezembro', 'destaque': True,
                'hospedagens': [
                    ('Pousada Maravilha', 'pousada', 1800, 'Vista para o Mar de Fora, piscina de borda infinita.'),
                    ('Hostel Ilha Azul', 'hostel', 220, 'Opção econômica perto da Vila dos Remédios.'),
                ],
                'avaliacoes': [
                    ('Marina S.', 5, 'Viagem dos sonhos! A Baía do Sancho é surreal, parece pintura.'),
                    ('Carlos E.', 4, 'Lugar incrível, mas se programe: tudo na ilha é bem caro.'),
                ],
            },
        ]

        criados = 0
        for item in dados:
            hospedagens = item.pop('hospedagens')
            avaliacoes = item.pop('avaliacoes')
            slug = item.pop('slug', None) or slugify(f'{item["nome"]}-{item["pais"]}')

            destino, novo = Destino.objects.get_or_create(slug=slug, defaults=item)
            if not novo:
                self.stdout.write(self.style.WARNING(f'· Já existia: {destino}'))
                continue

            for nome, tipo, preco, desc in hospedagens:
                Hospedagem.objects.create(destino=destino, nome=nome)
            for autor, nota, comentario in avaliacoes:
                Avaliacao.objects.create(destino=destino, nome_autor=autor,
                                         nota=nota, comentario=comentario)
            criados += 1
            self.stdout.write(self.style.SUCCESS(f'✔ Criado: {destino}'))

        self.stdout.write(self.style.SUCCESS(
            f'Pronto! {criados} destino(s) de exemplo criado(s).'))
