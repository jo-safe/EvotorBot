:: Создание службы Windows
echo Создание службы Windows...
sc create EvotorReports binPath= "python C:\EvotorReports\script.py"
sc start EvotorReports

echo Настройка завершена!
echo Сервис запущен и настроен на автозапуск при перезагрузке системы.
echo Скрипт доступен по адресу: http://localhost:5000