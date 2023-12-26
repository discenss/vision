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

def read_bot_keys(file_path):
    with open(file_path, 'r') as file:
        first_line = file.readline().rstrip()
        second_line = file.readline().rstrip()

    return first_line, second_line

# Пример использования функции
file_path = 'file.txt'  # Укажите путь к вашему файлу
bot_id, payment_token = read_bot_keys(file_path)
bot = telebot.TeleBot(bot_id)

base_rep = """
🔓Початок: %s
🔓Зачинення: %s \n
  Загальний час роботи %s\n
🧍‍♂️ Відсутність на робочому місці:
%s
\n🧍‍♂Загальний час відсутності: %s хв\n
"""

sells_rep = """
📉Кількість продажів проекту:
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
    parser.add_argument('--debug', default=False, action='store_true', help='debugging mode')

    parsed_args = parser.parse_args(args)

    project_path = parsed_args.project
    source_path = parsed_args.source
    est_name = parsed_args.est
    server_id = parsed_args.id
    device = parsed_args.device
    debug = parsed_args.debug

    db = DB()
    converted_date = get_date_from_file(source_path)
    if converted_date == False:
        return str(y)

    converted_date = get_date_from_file(source_path)
    if converted_date == False:
        return str(y)
    try:
        if debug is False: weight = db.get_weights()
        LOGGER.info(str(datetime.datetime.now())[:-7] + ': Task started with params ' + str(y))
        if debug is False: db.set_start_task(server_id, db.get_id_est_by_name(parsed_args.est),
                                             parsed_args.source)
        if debug is False:
            frames_file = run(weights=weight, source=source_path, project=r'testing', imgsz=(1280, 1280), save_txt=True,
                          nosave=True,
                          device=device)
        else:
            no_save = True
            if project_path is not None: no_save = False
            else:
                project_path = 'testing'
                frames_file = run(weights='best.pt', source=source_path, project=project_path, imgsz=(1280, 1280), save_txt=True,nosave=no_save, device=device)

        if debug is False : db.set_end_task(server_id, db.get_id_est_by_name(parsed_args.est), parsed_args.source)
        if debug is False : os.remove(weight)

        LOGGER.info(str(datetime.datetime.now())[:-7] + ': Task finished with params ' + str(y))

        orders = []
        sum = 0
        mid = 0
        cash = 0
        card = 0

        time_from_file = get_time_from_file(source_path)
        if db.get_report_type(est_name) != 'none':
            orders, sum, mid, cash, card = parse_report(source_path[:-3] + 'json', est_name)
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
        data['sum'] = str(sum)
        if len(orders) > 0:
            formatted_report = formatted_report + sells_rep % (
                activities_formatted,
                len(orders),
                mid,
                sum,
                cash,
                card
            )
        users = db.get_users_list_for_est(est_name)

        user_message = f"\n___________________\n📈 Звіт за дату: {converted_date}\n Заклад: {est_name}\n" + formatted_report

        if debug is False:
            db.set_base_report(est_name, str(converted_date), generate_report_text(data))
            for user in users:
                tg_id = db.get_telegram_id(user)
                bot.send_message(tg_id, user_message)
        else:
            bot.send_message('440385834', user_message)

    except Exception as e:
        LOGGER.info(str(datetime.datetime.now())[:-7] + f': ERROR in task {source_path}: ' + str(e))
        traceback.print_exc()

    return str(y)


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
                        exit()
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
    main()
