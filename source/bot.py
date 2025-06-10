import logging, requests
import os
from telegram.ext import Updater, CommandHandler, MessageHandler
from datetime import datetime

class TelegramBot:
    def __init__(self, token: str, script_url: str):
        self.token = token
        self.script_url = script_url
        self.setup_logging()
        self.updater = Updater(token=token)
        self.dp = self.updater.dispatcher
        
        self.dp.add_handler(CommandHandler('set_schedule', self.set_schedule))
        self.dp.add_handler(CommandHandler('stat_today', self.get_stat_today))
        self.dp.add_handler(CommandHandler('force_export', self.force_export))
        self.dp.add_handler(CommandHandler('help', self.help))
        
    def setup_logging(self):
        logging.basicConfig(
            filename='bot_logs.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        
    def start(self):
        self.updater.start_polling()
        logging.info('Бот запущен')
        
    def stop(self):
        self.updater.stop()
        logging.info('Бот остановлен')
        
    def send_command_to_script(self, command: str) -> str:
        try:
            response = requests.post(self.script_url, json={'command': command})
            if response.status_code == 200:
                return response.json().get('result', 'OK')
            return f'Ошибка: {response.status_code}'
        except Exception as e:
            logging.error(f'Ошибка при отправке команды: {str(e)}')
            return 'Ошибка при отправке команды'
            
    def set_schedule(self, update, context):
        try:
            time = context.args[0]
            result = self.send_command_to_script(f'set_schedule {time}')
            update.message.reply_text(result)
        except IndexError:
            update.message.reply_text('Используйте: /set_schedule HH:MM')
            
    def get_stat_today(self, update, context):
        result = self.send_command_to_script('stat_today')
        update.message.reply_text(result)
        
    def force_export(self, update, context):
        result = self.send_command_to_script('force_export')
        update.message.reply_text(result)
        
    def help(self, update, context):
        help_text = """
        Доступные команды:
        /set_schedule HH:MM - установить время ежедневной выгрузки
        /stat_today - получить статистику за сегодня
        /force_export - немедленная выгрузка данных
        /help - показать это сообщение
        """
        update.message.reply_text(help_text)

if __name__ == '__main__':
    token = os.environ.get('TELEGRAM_TOKEN')
    script_url = os.environ.get('SCRIPT_URL')
    
    if not token or not script_url:
        print('Необходимо установить переменные окружения TELEGRAM_TOKEN и SCRIPT_URL')
        exit(1)
        
    bot = TelegramBot(token, script_url)
    try:
        bot.start()
    except KeyboardInterrupt:
        bot.stop()
