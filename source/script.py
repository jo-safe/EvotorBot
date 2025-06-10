import os
import logging
import datetime
import schedule
import time
from typing import Dict, List
from flask import Flask, request, jsonify
from telegram.ext import Updater, CommandHandler, MessageHandler
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import requests

app = Flask(__name__)

class EvotorReportSystem:
    def __init__(self):
        self.setup_logging()
        
        self.config = {
            'evotor_token': self.load_config('evotor_token.txt'),
            'telegram_token': self.load_config('telegram_token.txt'),
            'google_creds_path': 'google_credentials.json',
            'schedule_time': self.load_config('schedule_time.txt', default='23:00'),
            'log_path': 'logs/system.log'
        }
        
        self.telegram_bot = self.setup_telegram_bot()
        self.gs_client = self.setup_google_sheets()
        self.evotor_api = self.setup_evotor_api()
        
        self.setup_scheduler()
        
        os.makedirs('logs', exist_ok=True)

    def setup_logging(self):
        logging.basicConfig(
            filename=self.config['log_path'],
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

    def load_config(self, filename: str, default=None) -> str:
        try:
            with open(filename, 'r') as f:
                return f.read().strip()
        except FileNotFoundError:
            if default is None:
                raise ValueError(f"Конфигурационный файл {filename} не найден")
            return default

    def setup_telegram_bot(self) -> Updater:
        updater = Updater(token=self.config['telegram_token'])
        
        dp = updater.dispatcher
        
        dp.add_handler(CommandHandler('set_schedule', self.handle_set_schedule))
        dp.add_handler(CommandHandler('stat_today', self.handle_stat_today))
        dp.add_handler(CommandHandler('force_export', self.handle_force_export))
        dp.add_handler(CommandHandler('help', self.handle_help))
        
        return updater

    def setup_google_sheets(self):
        scope = ['https://spreadsheets.google.com/feeds',
                'https://www.googleapis.com/auth/drive']
        creds = ServiceAccountCredentials.from_json_keyfile_name(
            self.config['google_creds_path'], scope)
        return gspread.authorize(creds)

    def setup_evotor_api(self):
        headers = {
            'Authorization': f'Bearer {self.config["evotor_token"]}'
        }
        return requests.Session()
        
    def setup_scheduler(self):
        schedule.every().day.at(self.config['schedule_time']).do(
            self.export_data)

    def handle_set_schedule(self, bot, update):
        """Обработчик команды /set_schedule"""
        try:
            new_time = update.message.text.split()[1]
            schedule.clear()
            schedule.every().day.at(new_time).do(self.export_data)
            
            with open('schedule_time.txt', 'w') as f:
                f.write(new_time)
                
            update.message.reply_text(f'Расписание обновлено: {new_time}')
        except IndexError:
            update.message.reply_text('Используйте: /set_schedule HH:MM')

    def handle_stat_today(self, bot, update):
        """Обработчик команды /stat_today"""
        today = datetime.datetime.now().strftime('%Y-%m-%d')
        url = 'https://api.evotor.ru/retail/api/v1/sales'
        params = {'date': today}
        
        response = self.evotor_api.get(url, params=params)
        if response.status_code == 200:
            sales = response.json()['items']
            summary = self.calculate_summary(sales)
            update.message.reply_text(summary)
        else:
            update.message.reply_text('Ошибка при получении данных')

    def handle_force_export(self, bot, update):
        """Обработчик команды /force_export"""
        success = self.export_data()
        if success:
            spreadsheet_url = self.gs_client.open('Отчеты').url
            update.message.reply_text(
                f'Выгрузка завершена, вот таблица: {spreadsheet_url}')

    def handle_help(self, bot, update):
        """Обработчик команды /help"""
        help_text = """
        Доступные команды:
        /set_schedule HH:MM - установить время ежедневной выгрузки
        /stat_today - получить статистику за сегодня
        /force_export - немедленная выгрузка данных
        /help - показать это сообщение
        """
        update.message.reply_text(help_text)

    def export_data(self):
        """Экспорт данных в Google Sheets"""
        try:
            spreadsheet = self.gs_client.open('Отчеты')
            
            sales_sheet = spreadsheet.worksheet('Продажи')
            sales_data = self.get_sales_data()
            sales_sheet.append_rows(sales_data, insert_data_option='INSERT_ROWS')
            
            returns_sheet = spreadsheet.worksheet('Возвраты')
            returns_data = self.get_returns_data()
            returns_sheet.append_rows(returns_data, insert_data_option='INSERT_ROWS')
            
            inventory_sheet = spreadsheet.worksheet('Остатки')
            inventory_data = self.get_inventory_data()
            inventory_sheet.append_rows(inventory_data, insert_data_option='INSERT_ROWS')
            
            employees_sheet = spreadsheet.worksheet('Сотрудники')
            employees_data = self.get_employees_data()
            employees_sheet.append_rows(employees_data, insert_data_option='INSERT_ROWS')
            
            return True
        except Exception as e:
            logging.error(f'Ошибка при экспорте данных: {str(e)}')
            return False

    def get_sales_data(self) -> List[List]:
        today = datetime.datetime.now().strftime('%Y-%m-%d')
        url = 'https://api.evotor.ru/retail/api/v1/sales'
        params = {'date': today}
        
        response = self.evotor_api.get(url, params=params)
        if response.status_code == 200:
            sales = response.json()['items']
            return [[
                sale['date'],
                sale['time'],
                sale['receipt_number'],
                sale['cashier_name'],
                sale['product_name'],
                sale['quantity'],
                sale['price'],
                sale['discount_amount'],
                sale['total_amount'],
                sale['vat_rate'],
                sale['payment_method']
            ] for sale in sales]
        return []

    def get_returns_data(self) -> List[List]:
        today = datetime.datetime.now().strftime('%Y-%m-%d')
        url = 'https://api.evotor.ru/retail/api/v1/returns'
        params = {'date': today}
        
        response = self.evotor_api.get(url, params=params)
        if response.status_code == 200:
            returns = response.json()['items']
            return [[
                ret['date'],
                ret['time'],
                ret['product_name'],
                ret['quantity'],
                ret['amount'],
                ret['cashier_name']
            ] for ret in returns]
        return []

    def get_inventory_data(self) -> List[List]:
        url = 'https://api.evotor.ru/retail/api/v1/products'
        
        response = self.evotor_api.get(url)
        if response.status_code == 200:
            products = response.json()['items']
            return [[
                prod['name'],
                prod['article'],
                prod['quantity']
            ] for prod in products]
        return []

    def get_employees_data(self) -> List[List]:
        url = 'https://api.evotor.ru/retail/api/v1/employees'
        
        response = self.evotor_api.get(url)
        if response.status_code == 200:
            employees = response.json()['items']
            return [[
                emp['name'],
                emp['id'],
                emp['checks_count'],
                emp['total_amount'],
                emp['average_check']
            ] for emp in employees]
        return []

    def calculate_summary(self, sales: List[Dict]) -> str:
        total_sales = len(sales)
        total_amount = sum(float(sale['total_amount']) for sale in sales)
        avg_check = total_amount / total_sales if total_sales > 0 else 0
        
        returns = [s for s in sales if float(s['total_amount']) < 0]
        total_returns = len(returns)
        returns_amount = abs(sum(float(r['total_amount']) for r in returns))
        
        return f"""
Продаж: {total_sales}
Выручка: {total_amount:.2f}₽
Средний чек: {avg_check:.2f}₽
Возвраты: {total_returns} (на {returns_amount:.2f}₽)
"""

@app.route('/api/commands', methods=['POST'])
def handle_command():
    data = request.get_json()
    if 'command' not in data:
        return jsonify({'error': 'Command not provided'}), 400
    
    command = data['command']
    if command == 'set_schedule':
        if 'time' not in data:
            return jsonify({'error': 'Time not provided'}), 400
        system.config['schedule_time'] = data['time']
        with open('schedule_time.txt', 'w') as f:
            f.write(data['time'])
        return jsonify({'result': 'Schedule updated'})
    
    elif command == 'stat_today':
        return jsonify({'result': system.get_stat_today()})
    
    elif command == 'force_export':
        success = system.export_data()
        return jsonify({'result': 'OK' if success else 'Error'})
    
    return jsonify({'error': 'Unknown command'}), 400

if __name__ == '__main__':
    system = EvotorReportSystem()
    system.telegram_bot.start_polling()
    
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)
    except KeyboardInterrupt:
        system.telegram_bot.stop()
