@echo off
setlocal enabledelayedexpansion

echo Установка Python и зависимостей...
winget install Python.Python.3
python -m pip install --upgrade pip
pip install flask python-telegram-bot gspread oauth2client requests schedule

echo Создание структуры проекта...
mkdir C:\EvotorReports
mkdir C:\EvotorReports\config
mkdir C:\EvotorReports\logs

echo Настройка брандмауэра...
netsh advfirewall firewall add rule name="Evotor Reports" dir=in action=allow protocol=TCP localport=5000