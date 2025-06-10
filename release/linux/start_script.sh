echo "Создание системного сервиса..."
cat > /etc/systemd/system/evotor_reports.service << EOF
[Unit]
Description=Evotor Reports Service
After=network.target

[Service]
User=root
WorkingDirectory=/opt/evotor_reports
ExecStart=/usr/bin/python3 /opt/evotor_reports/script.py
Restart=always

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl start evotor_reports
sudo systemctl enable evotor_reports

echo "Настройка завершена!"
echo "Сервис запущен и настроен на автозапуск при перезагрузке системы."
echo "Скрипт доступен по адресу: http://localhost:5000"