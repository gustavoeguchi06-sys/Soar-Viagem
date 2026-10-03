"""Gunicorn da Soar no VPS (usado por deploy/soar.service).

Só escuta no próprio servidor: quem fala com a internet é o Nginx, que repassa
para cá. Assim o Gunicorn nunca fica exposto direto.
"""
import multiprocessing

bind = '127.0.0.1:8000'

# 2 x núcleos + 1 é a conta usual; num VPS de 1 núcleo dá 3 processos.
workers = multiprocessing.cpu_count() * 2 + 1

# Envio de vídeo pelo painel (até ~105 MB) pode levar mais que os 30 s padrão.
timeout = 120
graceful_timeout = 30

# Recicla o processo de tempos em tempos (evita vazamento de memória lento).
max_requests = 1000
max_requests_jitter = 100

# Logs: acesso e erro em arquivo (o logrotate do Ubuntu gira /var/log/soar/*.log
# com o deploy/logrotate-soar).
accesslog = '/var/log/soar/gunicorn-acesso.log'
errorlog = '/var/log/soar/gunicorn-erro.log'
loglevel = 'info'

# O IP real do visitante vem do Nginx (X-Forwarded-For); só confia no Nginx local.
forwarded_allow_ips = '127.0.0.1'
