cd /opt/evotor_reports
nohup python3 bot.py > bot.log 2>&1 &

BOT_PID=$!
echo $BOT_PID > bot.pid
echo "Бот запущен с PID: $BOT_PID"