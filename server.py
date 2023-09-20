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

def f(x, y):

    weight = get_params()['model_path']
    est_name = "Pekarnya"
    #script = os.path.join(os.getcwd(), 'detect.py')
    #if os.path.isfile(os.path.join(os.getcwd(), 'detect.py')):
    #    params = [sys.executable, script, weights, '--save-txt', '--device=' + get_params()['device']] + str(y).split(' ')
    #    print(str(datetime.datetime.now()) + ': Task started with params ' + str(y))
    #    process = Popen(params, stdout=PIPE, stderr=PIPE)
    #    stdout, stderr = process.communicate()
    #    #print(stdout)
    #    #print(stderr)
    #r = vars([weights, '--save-txt', '--device=' + get_params()['device']])

    db = DB()
    args = y.split()

    parser = argparse.ArgumentParser()
    parser.add_argument("--project", type=str, help="Path to project")
    parser.add_argument("--source", type=str, help="Path to source")
    parser.add_argument("--est", type=str, help="Path to source")

    parsed_args = parser.parse_args(args)

    project_path = parsed_args.project
    source_path = parsed_args.source
    est_name = parsed_args.est

    converted_date = get_date_from_file(source_path)
    #print(est_name)
    if converted_date == False:
        return str(y)

    LOGGER.info(str(datetime.datetime.now())[:-7] + ': Task started with params ' + str(y))
    frames_file = run(weights=weight, source=source_path, project=project_path, imgsz=(1280, 1280), save_txt=True, nosave=True, device=get_params()['device'])
    #frames_file = r"E:\dev\sources\testing\exp17\labels\2_2023-08-01_08-00-01.txt"
    LOGGER.info(str(datetime.datetime.now())[:-7] + ': Task finished with params ' + str(y))
    #print(frames_file)
    #print(source_path[:-3] + 'json')
    orders = parse_report(source_path[:-3] + 'json', est_name)
    text_base_report = create_report(frames_file, orders, source_path[:-4] + '.xspf', get_time_from_file(source_path).hour)
    result = '\n'.join(text_base_report)
    db.set_base_report(est_name, str(converted_date), result)
    users = db.get_users_list_for_est(est_name)
    user_message = f"📈 Отчёт за дату: {converted_date}\n Заведение: {est_name}\n" + result

    for user in users:
        tg_id = db.get_telegram_id(user)
        bot.send_message(tg_id, user_message)

    return str(y)

def clb(x):

    test = 'asd'

def main():


    with Pool(processes=int(get_params()['threads'])) as pool:
        address = ('10.100.94.60', 8443)  # family is deduced to be 'AF_INET'
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
