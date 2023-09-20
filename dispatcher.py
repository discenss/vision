import os.path
from multiprocessing.connection import Client
from utils.general import LOGGER

import schedule
import time
from utils.general import LOGGER
from db import DB
import re
import datetime
from datetime import date

res=r'E:\dev\sources\testing'

def get_date_from_file(source_path):
    match = re.search(r'(\d{4}-\d{2}-\d{2})', source_path)
    if match:
        date_string = match.group(1)
        converted_date = datetime.datetime.strptime(date_string, '%Y-%m-%d').date()
        return converted_date
        #print("Извлеченная дата:", converted_date)
    else:
        return False

def run_processing():

    print(" Processing started")
    db = DB()
    db.cur.execute(f"SELECT * FROM ESTABLISHMENTS")
    rows = db.cur.fetchall()
    list_not_resp = []
    for i in range(len(rows)):
        id, name, adress, passw, license_id, owner_id, report_type, path, date = rows[i]
        if path!= None and os.path.isdir(path):
            for file in os.listdir(path):
                if file.endswith('.mp4') and get_date_from_file(file)\
                        and os.path.isfile(os.path.join(path, file)[:-3]+'json'):
                    date_string = get_date_from_file(file)
                    if date_string:
                        date = str(date_string)
                        # Формируем запрос на выборку данных из таблицы по дате
                        query = f"SELECT * FROM REPORT WHERE REALDATE = '{date}' AND ESTABLISHMENT_ID = {id}"
                        # Выполняем запрос и получаем результат
                        db.cur.execute(query)

                        try:
                            d = db.cur.fetchall()
                            if len(d) > 0:
                                continue

                            while True:
                                ip_server = db.get_server_for_task(list_not_resp)

                                if len(ip_server) < 1:
                                    return ''

                                try:
                                    address = ('10.100.94.60', 8443)
                                    conn = Client(address)
                                    command = f"--source={os.path.join(path, file)} --project={res} --est={name}"
                                    print(command)
                                    conn.send(command)
                                    conn.send('close')
                                    conn.close()
                                    break
                                except:
                                    LOGGER.info(str(datetime.datetime.now()[:-7]) + " Not connected to server " + ip_server)
                                    list_not_resp.append(ip_server)
                                    pass
                                    continue

                        except:
                            pass

    else:
        return None

# Планирование задачи на выполнение каждый день в определенное время
schedule.every().day.at("00:00").do(run_processing)

def main():
    run_processing()
    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == '__main__':
    #bot.polling(none_stop=True, interval=0)  # обязательная для работы бота часть
    main()
