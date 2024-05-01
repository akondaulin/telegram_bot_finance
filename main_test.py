import telebot
from telebot import types
from datetime import datetime
import psycopg2
from db_config import dbname, user, password, port, host
from config import TOKEN

bot = telebot.TeleBot(TOKEN)

# Обработчик команды /start
@bot.message_handler(commands=['start'])
def handle_start(message):
    main_menu(message)

# Главное меню
def main_menu(message):
    markup = types.ReplyKeyboardMarkup()
    btn_start = types.KeyboardButton('/start')
    btn_stats = types.KeyboardButton('/stats')
    markup.row(btn_start, btn_stats)
    bot.send_message(message.chat.id, 'Главное меню', reply_markup=markup)

# Обработчик команды /stats
@bot.message_handler(commands=['stats'])
def stats_menu(message):
    markup = types.ReplyKeyboardMarkup()
    btn_today = types.KeyboardButton('Сводка расходов за сегодня')
    btn_yesterday = types.KeyboardButton('Сводка расходов за вчера')
    btn_week = types.KeyboardButton('Сводка расходов за неделю')
    btn_month = types.KeyboardButton('Сводка расходов с начала месяца')
    markup.row(btn_today, btn_yesterday)
    markup.row(btn_week, btn_month)
    bot.send_message(message.chat.id, 'Выберите период для сводки расходов', reply_markup=markup)

# Обработчик выбора периода для сводки расходов
@bot.message_handler(func=lambda message: message.text in ['Сводка расходов за сегодня', 'Сводка расходов за вчера',
                                                           'Сводка расходов за неделю', 'Сводка расходов с начала месяца'])
def show_stats(message):
    conn = psycopg2.connect(dbname=dbname, user=user, password=password, host=host, port=port)
    cur = conn.cursor()
    
    if message.text == 'Сводка расходов за сегодня':
        sql = "SELECT SUM(amount) AS total_cost FROM finance.costs WHERE date = CURRENT_DATE"
    elif message.text == 'Сводка расходов за вчера':
        sql = "SELECT SUM(amount) AS total_cost FROM finance.costs WHERE date = CURRENT_DATE - INTERVAL '1 day'"
    elif message.text == 'Сводка расходов за неделю':
        sql = "SELECT SUM(amount) AS total_cost FROM finance.costs WHERE date >= CURRENT_DATE - INTERVAL '7 days'"
    elif message.text == 'Сводка расходов с начала месяца':
        sql = "SELECT SUM(amount) AS total_cost FROM finance.costs WHERE date >= DATE_TRUNC('month', CURRENT_DATE)"
    
    cur.execute(sql)
    total_cost = cur.fetchone()[0]
    if total_cost is None:
        total_cost = 0
    bot.send_message(message.chat.id, f'Сумма расходов: {total_cost}')
    
    cur.close()
    conn.close()

# Обработчик введения суммы
@bot.message_handler(func=lambda message: message.text.isdigit())
def save_amount(message):
    amount = message.text
    current_date = datetime.now()
    save_to_database(current_date, amount)
    bot.send_message(message.chat.id, 'Сумма успешно сохранена!')
    main_menu(message) 

# Сохранение данных в базу данных
def save_to_database(date, amount):
    conn = psycopg2.connect(dbname=dbname, user=user, password=password, host=host, port=port)
    cur = conn.cursor()
    sql = "INSERT INTO finance.costs (date, amount) VALUES (%s, %s)"
    values = (date, amount)
    cur.execute(sql, values)
    conn.commit()
    cur.close()
    conn.close()

# Запуск бота
bot.infinity_polling()
