import multiprocessing.pool
from multiprocessing import Pool, TimeoutError
from subprocess import Popen, PIPE

import os
import time
import subprocess
from multiprocessing.connection import Listener
import sys
import datetime
from detect import run
import argparse
from parsing import create_report, parse_report
from db import DB
import telebot
from telebot import types
import re
import logging
from utils.general import LOGGER

bot = telebot.TeleBot('6560876647:AAGZXlZDeCazV8vQ9Wf6NZlqpJV7enc1olM')

base_rep = """
🔓Открытие: %s
🔓Закрыто: %s \n
🧍‍♂️ Нет на рабочем месте:
%s
\n🧍‍♂️Общее время отсутствия: %s мин\n
  Общее время работы %s
"""

sells_rep = """
\n📉Количество продаж проекта:
%s 

Итого продаж: %s 
🧾Средний чек проекта: %s грн.
💸Выручка : %s грн 
"""

def get_params():
    srv_cfg = {}
    if ( len(sys.argv) == 2 and os.path.isfile( sys.argv[1]) ):
        with open(r'server.cfg', 'rt') as f:
            for line in f.read().split('\n'):
                srv_cfg[line.split(' & ')[0]] = line.split('&')[1]
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
        frames_file = run(weights=weight, source=source_path, project=r'E:\dev\sources\testing', imgsz=(1280, 1280), save_txt=True, nosave=True, device=device)
        db.set_end_task(server_id, db.get_id_est_by_name(parsed_args.est), parsed_args.source)
        os.remove(weight)
        #frames_file = r"E:\dev\sources\testing\exp243\3_2023-10-11_11-00-00.txt"
        LOGGER.info(str(datetime.datetime.now())[:-7] + ': Task finished with params ' + str(y))
        orders, sum = parse_report(source_path[:-3] + 'json', est_name)
        data = create_report(frames_file, orders, source_path[:-4] + '.xspf', get_time_from_file(source_path).hour)
        data['sum'] = str(sum)
        count = 1
        if len(orders) > 0:
            count = len(orders)
        else:
            count = 1
        away_periods_formatted = "\n".join(data['away_periods'])
        activities_formatted = "\n".join(data['activities'])
        time_open = datetime.datetime.strptime(data['opening_time'], "%H:%M:%S")
        time_close = datetime.datetime.strptime(data['closing_time'], "%H:%M:%S")
        formatted_report = base_rep % (
            data['opening_time'],
            data['closing_time'],
            away_periods_formatted,
            data['total_away'],
            str(time_close - time_open)
        )

        if len(orders) > 0:
            formatted_report = formatted_report + sells_rep % (
                activities_formatted,
                count,
                int(sum / count),
                sum
            )
        users = db.get_users_list_for_est(est_name)

        user_message = f"📈 Отчёт за дату: {converted_date}\n Заведение: {est_name}\n" + formatted_report

        db.set_base_report(est_name, str(converted_date), generate_report_text(data))
        for user in users:
            tg_id = db.get_telegram_id(user)
            bot.send_message(tg_id, user_message)
    except Exception as e:
        LOGGER.info(f'ERROR in task {source_path}: ' + str(e))


    return str(y)

def clb(x):

    test = 'asd'

def main():


    with Pool(processes=5) as pool:
        address = ('127.0.0.1', 1111)  # family is deduced to be 'AF_INET'
        listener = Listener(address)
        LOGGER.info('Server started, waiting for connections...')
        #print('Server started, waiting for connections...')
        while True:
            conn = listener.accept()
            while True:
                msg = conn.recv()
                if msg == 'close':
                    conn.close()
                    break
                if msg == 'close_server':
                    conn.close()
                    exit(0)
                #print('Task added in pool with params -' + msg)
                pool.apply_async(f, (os.getpid(), msg))

    print(str(datetime.datetime.now()) + ' Server started, waiting for connections')


if __name__ == '__main__':
    #bot.polling(none_stop=True, interval=0)  # обязательная для работы бота часть
    main()
