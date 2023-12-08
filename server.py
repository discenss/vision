from multiprocessing import Pool, TimeoutError

import os
from multiprocessing.connection import Listener
import sys
import datetime
import argparse
from parsing import create_report, parse_report
from db import DB
import telebot
import re
from utils.general import LOGGER
import traceback
from detect import run

bot = telebot.TeleBot('6560876647:AAGZXlZDeCazV8vQ9Wf6NZlqpJV7enc1olM')

base_rep = """
🔓Початок: %s
🔓Зачинення: %s \n
  Загальний час роботи %s\n
🧍‍♂️ Відсутність на робочому місці:
%s
\n🧍‍♂Загальний час відсутності: %s мин\n
"""

sells_rep = """
\n📉Кількість продажів проекту:
%s 

Продажів загалом: %s 
🧾Средній чек проекту: %s грн.
💸Сумма загалом : %s грн
💵Готівкою : %s грн
💳Карткою :  %s грн 
"""

def get_params(file_name):
    srv_cfg = {}
    if len(sys.argv) == 2 and os.path.isfile(sys.argv[1]):
        with open(file_name, 'rt') as f:
            for line in f:
                line = line.strip()
                # Проверяем, что строка не пустая и содержит разделитель
                if line and ' & ' in line:
                    parts = line.split(' & ')
                    if len(parts) == 2:
                        key, value = parts
                        srv_cfg[key] = value
    return srv_cfg

def get_date_from_file(source_path):
    match = re.search(r'(\d{4}-\d{2}-\d{2})', source_path)
    if match:
        date_string = match.group(1)
        converted_date = datetime.datetime.strptime(date_string, '%Y-%m-%d').date()
        return converted_date
    else:
        return False

def get_time_from_file(source_path):
    pattern = r'(\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2})'

    # Поиск совпадений в имени файла
    match = re.search(pattern, source_path)
    if match:
        date_string = match.group(1)
        converted_time = datetime.datetime.strptime(date_string, "%Y-%m-%d_%H-%M-%S")
        return converted_time.time()
    else:
        return False

def generate_report_text(report_data):
    report_lines = [
        f"Opening : {report_data['opening_time']}",
        f"Closing  : {report_data['closing_time']}",
    ]

    for start in report_data['away_periods']:
        report_lines.append(f"Away: " + start)

    report_lines.append("Total away : " + report_data['total_away'])

    for start in report_data['activities']:
        report_lines.append(f"Activity : {start}")

    report_lines.append("Sum : " + report_data['sum'])
    return '\n'.join(report_lines)


def f(x, y):


    db = DB()
    args = y.split()

    parser = argparse.ArgumentParser()
    parser.add_argument("--project", type=str, help="Path to project")
    parser.add_argument("--source", type=str, help="Path to source")
    parser.add_argument("--est", type=str, help="Est id")
    parser.add_argument("--id", type=str, help="Server id")
    parser.add_argument("--device", type=str, default='0', help="index device")

    parsed_args = parser.parse_args(args)

    project_path = parsed_args.project
    source_path = parsed_args.source
    est_name = parsed_args.est
    server_id = parsed_args.id
    device = parsed_args.device

    converted_date = get_date_from_file(source_path)
    if converted_date == False:
        return str(y)
    try:
        weight = db.get_weights()
        LOGGER.info(str(datetime.datetime.now())[:-7] + ': Task started with params ' + str(y))
        db.set_start_task( server_id, db.get_id_est_by_name(parsed_args.est), parsed_args.source)
        frames_file = run(weights=weight, source=source_path, project=r'testing', imgsz=(1280, 1280), save_txt=True, nosave=True, device=device)
        db.set_end_task(server_id, db.get_id_est_by_name(parsed_args.est), parsed_args.source)
        os.remove(weight)
        #frames_file = r"E:\dev\vision\testing\exp27\3_2023-11-08_11-00-00.txt"
        LOGGER.info(str(datetime.datetime.now())[:-7] + ': Task finished with params ' + str(y))

        orders = []
        sum = 0
        mid = 0
        cash = 0
        card = 0

        if db.get_report_type(est_name) != 'none':
            orders, sum, mid, cash, card = parse_report(source_path[:-3] + 'json', est_name)
            time_from_file = get_time_from_file(source_path)
            print(time_from_file)
            if time_from_file is False:
                raise ValueError("Ошибка получения времени из файла")


        data = create_report(frames_file, orders, source_path[:-4] + '.xspf', time_from_file.hour)


        away_periods_formatted = "\n".join(data['away_periods'])
        activities_formatted = "\n".join(data['activities'])
        time_open = datetime.datetime.strptime(data['opening_time'], "%H:%M:%S")
        time_close = datetime.datetime.strptime(data['closing_time'], "%H:%M:%S")
        formatted_report = base_rep % (
            data['opening_time'],
            data['closing_time'],
            str(time_close - time_open),
            away_periods_formatted,
            data['total_away']
        )

        if len(orders) > 0:
            formatted_report = formatted_report + sells_rep % (
                activities_formatted,
                count,
                mid,
                sum,
                cash,
                card
            )
        users = db.get_users_list_for_est(est_name)

        user_message = f"📈 Звіт за дату: {converted_date}\n Заклад: {est_name}\n" + formatted_report

        db.set_base_report(est_name, str(converted_date), generate_report_text(data))
        for user in users:
            tg_id = db.get_telegram_id(user)
            bot.send_message(tg_id, user_message)
    except Exception as e:
        LOGGER.info(str(datetime.datetime.now())[:-7] + f': ERROR in task {source_path}: ' + str(e))
        traceback.print_exc()

    return str(y)

def clb(x):

    test = 'asd'

def main():


    with Pool(processes=int(get_params(sys.argv[1])['threads'])) as pool:
        address = (get_params(sys.argv[1])['ip'], int(get_params(sys.argv[1])['port']))  # family is deduced to be 'AF_INET'
        listener = Listener(address)
        LOGGER.info('Server started, waiting for connections...')
        running = True

        def handle_connection(conn):
            while True:
                try:
                    msg = conn.recv()
                    if msg == 'close':
                        conn.close()
                        break
                    if msg == 'close_server':
                        global running
                        running = False
                        conn.close()
                        break
                    # logging.info('Task added in pool with params -' + msg)
                    pool.apply_async(f, (os.getpid(), msg))
                except EOFError:
                    # Handle client disconnect
                    break
                except Exception as e:
                    LOGGER.error("Error during message receiving: %s", e)
                    break

        while running:
            conn = listener.accept()
            handle_connection(conn)

        # Очистка ресурсов после завершения работы
        pool.close()
        pool.join()

if __name__ == '__main__':
    #bot.polling(none_stop=True, interval=0)  # обязательная для работы бота часть
    main()
