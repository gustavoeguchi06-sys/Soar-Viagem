@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Soar - servidor
echo.
echo  ===== SOAR OPERADORA =====
echo.
if exist ".venv\Scripts\python.exe" (set PY=.venv\Scripts\python.exe) else (set PY=python)
echo Iniciado em %date% %time% > rodar.log
echo python: %PY% >> rodar.log
echo [1/3] Preparando o banco...
%PY% manage.py migrate >> rodar.log 2>&1
if errorlevel 1 (
  echo.
  echo  ERRO ao preparar o banco. Veja o arquivo rodar.log
  type rodar.log
  pause
  exit /b 1
)
echo [2/3] Apagando dados vencidos (aviso de privacidade)...
%PY% manage.py expurgar_dados >> rodar.log 2>&1
echo [3/3] Ligando o servidor...
echo.
echo  Site:   http://127.0.0.1:8000/
echo  Painel: http://127.0.0.1:8000/painel/
echo.
echo  O navegador abre sozinho em alguns segundos.
echo  Deixe esta janela aberta. Para parar: Ctrl+C
echo.
start "" /min cmd /c "timeout /t 5 /nobreak >nul & start "" http://127.0.0.1:8000/"
%PY% manage.py runserver 2>> rodar.log
echo.
echo  O servidor parou. Veja o rodar.log se houve erro.
type rodar.log
pause
