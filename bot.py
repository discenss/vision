import telebot
from telebot import types
from datetime import datetime
from db import DB
from telebot.types import LabeledPrice, ShippingOption
import time

# 6560876647:AAGZXlZDeCazV8vQ9Wf6NZlqpJV7enc1olM

payment_token = "1711243933:LIVE:7T64-2KCi-TyH3-kcN7"
#PRODUCT_COST = 500  # Example cost in the smallest units (e.g., cents for USD)
#SHIPPING_COST = 5  # Example shipping cost

bot = telebot.TeleBot('6560876647:AAGZXlZDeCazV8vQ9Wf6NZlqpJV7enc1olM')


report_for_date = 'Введите дату в формате ГГГГ-ММ-ДД (например 1991-08-24)'
report_for_date_or_exit = "Введите дату в формате ГГГГ-ММ-ДД (например 1991-08-24) или /menu для выхода"
est_name_and_password_for_subsc = "Введите название_заведения и пароль через пробел. Hапример:\n MyBar MyPassword"
top_up_account = "Введите сумму пополнения"

def send_bot_message(message, tg_id):
    bot.send_message(tg_id, message)

@bot.pre_checkout_query_handler(func=lambda query: True)
def process_pre_checkout(query):
    bot.answer_pre_checkout_query(pre_checkout_query_id=query.id, ok=True)

@bot.message_handler(content_types=['successful_payment'])
def handle_successful_payment(message):
    db = DB()
    db.addmomey_for_tg_user(message.from_user.id, message.successful_payment.total_amount / 100)
    bot.reply_to(message, "Вы успешно пополнили счёт. Баланс %s" % db.get_money_for_tg_user(message.from_user.id))
    show_main_menu(message)

def show_main_menu(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)  # создание новых кнопок
    btn1 = types.KeyboardButton('Профиль')
    btn2 = types.KeyboardButton('Получить отчёт за дату')
    btn3 = types.KeyboardButton('Подписаться на регулярный отчёт')
    btn4 = types.KeyboardButton('Написать в сервис')
    btn5 = types.KeyboardButton('Пополнить счёт')
    #btn6 = types.KeyboardButton('Проверить состояние счёта')

    markup.add(btn1, btn2, btn3, btn4, btn5)
    bot.send_message(message.from_user.id, 'Выберите нужное действие', reply_markup=markup)

@bot.message_handler(commands=['start'])
def start(message):

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("👋 Начать")
    markup.add(btn1)
    bot.send_message(message.from_user.id, "👋 Привет! Я твой бот для работы с видео наблюдением. \n"
                                           "/start - начать с начала\n"
                                           "/menu - показать меню ", reply_markup=markup)

@bot.message_handler(commands=['menu'])
def start(message):

    show_main_menu(message)

@bot.message_handler(func=lambda message: message.reply_to_message is not None and
                                          (message.reply_to_message.text == report_for_date or
                                            message.reply_to_message.text ==  report_for_date_or_exit))

@bot.message_handler(func=lambda message: message.reply_to_message is not None and
                                          message.reply_to_message.text == est_name_and_password_for_subsc)

@bot.message_handler(func=lambda message: message.reply_to_message is not None and
                                          message.reply_to_message.text == top_up_account)

def handle_reply(message):
    if message.reply_to_message.text == report_for_date or message.reply_to_message.text == report_for_date_or_exit:
        try:
            date = datetime.strptime(message.text, '%Y-%m-%d')
            bot.reply_to(message, f'Вы ввели правильный формат даты: {date}')
            bot.reply_to(message, f'Идёт проверка')
            bot.reply_to(message, f'Вы получите отчёт как только база данных будет готова')
            show_main_menu(message)

        except ValueError:
            bot.reply_to(message, 'Неверный формат даты.')
            markup = types.ForceReply(selective=False)
            bot.send_message(message.from_user.id, report_for_date_or_exit, reply_markup=markup)

    elif message.reply_to_message.text == est_name_and_password_for_subsc:
        if(len(message.text.split(' ')) ==2):
            name, passw = message.text.split(' ')
            bot.reply_to(message, f'Вы ввели название заведения: {name}\nПароль: {passw}')
            db = DB()
            res = db.subscribe_user_to_est(message.from_user.id, name, passw)
            if (res == 'success'):
                markup = types.ForceReply(selective=False)
                bot.send_message(message.from_user.id, f'Вы успешно подписаны на регулярный отчёт. Ожидайте следующего отчёта', reply_markup=markup)
            else:
                markup = types.ForceReply(selective=False)
                bot.send_message(message.from_user.id, res, reply_markup=markup)

            show_main_menu(message)
        else:
            bot.reply_to(message, f'Вы не ввели название_заведения и пароль')
            show_main_menu(message)
    elif message.reply_to_message.text == top_up_account:
        try:
            val = int(message.text)
            prices = [LabeledPrice(label='Product', amount=val * 100)]
            bot.send_invoice(
                chat_id=message.chat.id,
                title="Vision",
                description="A description about your product",
                provider_token=payment_token,  # Get this from your payment provider setup
                currency="UAH",
                is_flexible=False,  # True If you want to send a flexible invoice
                prices=prices,
                start_parameter="start_param",
                invoice_payload="payload"
            )
        except ValueError:
            bot.reply_to(message, 'Неверный формат числа')
            markup = types.ForceReply(selective=False)
            bot.send_message(message.from_user.id, top_up_account, reply_markup=markup)


@bot.message_handler(content_types=['text'])
def get_text_messages(message):

    if message.text == '👋 Начать':
        show_main_menu(message)

    elif message.text == 'Профиль':
        db = DB()
        est_subs = db.get_est_list_for_tg_user(message.from_user.id)
        messg = ''
        if est_subs is None:
            messg = 'Вы не подписаны ни на одно заведение\n'
        else:
            ests = ' '.join(est_subs)
            messg = 'Вы подписаны на заведения: ' + ests

        est_subs = db.get_est_name_by_owner_id(message.from_user.id)

        if est_subs is None:
            messg += " \nВы не подписаны ни на одно заведение"
        else:
            ests = ' '.join(est_subs)
            messg =  messg + '\nВы являетесь владельцем: ' + ests

        messg = messg + f"\nУ вас на счету {db.get_money_for_tg_user(message.from_user.id)} UAH"

        bot.send_message(message.from_user.id,
                         messg,
                         parse_mode='Markdown')



    elif message.text == 'Получить отчёт за дату':
        markup = types.ForceReply(selective=False)
        bot.send_message(message.from_user.id, report_for_date, reply_markup=markup)

    elif message.text == 'Подписаться на регулярный отчёт':
        markup = types.ForceReply(selective=False)
        bot.send_message(message.from_user.id, est_name_and_password_for_subsc, reply_markup=markup)

    elif message.text == 'Получить информацию про заведение':
        markup = types.ForceReply(selective=False)
        bot.send_message(message.from_user.id, "Введине название заведения и пароль",
                         reply_markup=markup)

    elif message.text == "Пополнить счёт":
        markup = types.ForceReply(selective=False)
        db = DB()
        #if db.is_tg_user_owner(message.from_user.id):
        bot.send_message(message.from_user.id, top_up_account,
                         reply_markup=markup)
       # else:
        #    bot.send_message(message.from_user.id,
        #                     "Вы не являетесь владельцем заведения",
        #                     parse_mode='Markdown')
        show_main_menu(message)

    elif message.text == "Проверить состояние счёта":
        db = DB()
        money = db.get_money_for_tg_user(message.from_user.id)
        if money is None:
            bot.send_message(message.from_user.id,
                             "Данные не найдены",
                             parse_mode='Markdown')
        else:
            bot.send_message(message.from_user.id,
                             f"На счету {money} гривен",
                             parse_mode='Markdown')


if __name__ == '__main__':
    while True:
        try:
            bot.polling(none_stop=True)
        except ConnectionError as e:
            print("Connection error, retrying...", e)
            time.sleep(15)