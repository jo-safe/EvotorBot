echo "Обновление системы..."
sudo apt-get update -y
sudo apt-get upgrade -y

echo "Установка Python и зависимостей..."
sudo apt-get install -y python3 python3-pip python3-dev

echo "Создание структуры проекта..."
mkdir -p /opt/evotor_reports/config
mkdir -p /opt/evotor_reports/logs

echo "Установка Python пакетов..."
pip3 install --upgrade pip
pip3 install flask python-telegram-bot gspread oauth2client requests schedule

echo "Настройка брандмауэра..."
sudo ufw allow 5000/tcp

echo "Настройка завершена."