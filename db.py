# -*- coding: utf-8 -*-
#import fdb
import os

import psycopg2
from psycopg2 import OperationalError
from datetime import datetime
from utils.general import LOGGER
import tempfile
def is_valid_date_format(s):
    try:
        datetime.strptime(s, '%Y-%m-%d')
        return True
    except ValueError:
        return False
class DB():
    def __init__(self):
        #con = fdb.connect(
        #    dsn=r'localhost:C:\Users\oleg.kalinin\Documents\VISION.FDB',
        #    user='SYSDBA',
        #    password='root',
        #    charset='UTF8'
        #)

        try:
            con = psycopg2.connect(
                user="postgres",
                password="root",
                host="192.168.231.1",
                port="5432",
                database="postgres",
                client_encoding='utf8'
            )
            self.con = con
        except OperationalError as e:
            print(f"The error '{e}' occurred")
            return None

        if con == None:
            raise ValueError("Connection is failed")

        self.con = con
        self.cur = con.cursor()

    def get_user_id_by_login(self, login):
        self.cur.execute(f"SELECT * FROM users WHERE login = '{login}'")
        rows = self.cur.fetchall()
        if len(rows) == 1:
            id, name, login, role, password, count, telegram_id = rows[0]
            return id
        else:
            return None

    def get_full_user_list(self):
        self.cur.execute(f"SELECT * FROM users")
        rows = self.cur.fetchall()
        id_s = []
        for row in rows:
            id, name, login, role, password, count, telegram_id = row
            id_s.append(telegram_id)
        return id_s

    def get_user_name_by_id(self, name):
        self.cur.execute(f"SELECT user_id FROM users WHERE \"NAME\" = '{name}'")
        rows = self.cur.fetchall()
        if len(rows) == 1:
            return str(rows[0][0])
        else:
            return None

    def get_user_id_by_tg_id(self, tg_id):
        self.cur.execute(f"SELECT user_id FROM users WHERE telegram_id = '{tg_id}'")
        rows = self.cur.fetchall()
        if len(rows) == 1:
            return str(rows[0][0])
        else:
            return None

    def get_report_type(self, name):
        self.cur.execute(f"SELECT * FROM ESTABLISHMENTS WHERE \"NAME\" = '{name}'")
        rows = self.cur.fetchall()
        if len(rows) == 1:
            id, name, adress, passw, license_id, owner_id, report_type, path, date, extra = rows[0]
            return report_type
        else:
            return None

    def get_id_est_by_name(self, name):
        self.cur.execute(f"SELECT * FROM ESTABLISHMENTS WHERE \"NAME\" = '{name}'")
        rows = self.cur.fetchall()
        if len(rows) == 1:
            id, name, adress, passw, license_id, owner_id, report_type, path, date, extra = rows[0]
            return id
        else:
            return None

    def set_base_report(self, est_name, realdate, baseinfo = None):
        self.cur = self.con.cursor()
        if is_valid_date_format(realdate):
            query = """
                   INSERT INTO REPORT (ESTABLISHMENT_ID, REALDATE, BASEINFO, BASE_DONE) 
    VALUES (%s, %s, %s, %s)
                """
            est_id = self.get_id_est_by_name(est_name)
            if (est_id!= None):
                #print(str(datetime.now().date()))
                self.cur.execute(query, (est_id, realdate, baseinfo, str(datetime.now().date())))
                self.con.commit()
                LOGGER.info(
                    str(datetime.now())[:-7] + f' Added report for {est_name} and date {realdate}')

    def update_base_report(self, est_name, realdate, baseinfo=None):
        self.cur = self.con.cursor()
        if is_valid_date_format(realdate):
            query = """
                UPDATE REPORT 
                SET BASEINFO = %s
                WHERE ESTABLISHMENT_ID = %s AND REALDATE = %s
            """
            est_id = self.get_id_est_by_name(est_name)
            if est_id is not None:
                self.cur.execute(query, (baseinfo, est_id, realdate))
                self.con.commit()
                LOGGER.info(str(datetime.now())[:-7] + f' Updated BASEINFO for {est_name} and date {realdate}')

    def get_est_info_by_name(self, est_name):
        self.cur.execute(f'SELECT * FROM establishments WHERE "NAME" = \'{est_name}\'')
        rows = self.cur.fetchall()
        if len(rows) == 1:
            id, name, adress, passw, license_id, owner_id, report_type, path, date, extra = rows[0]
        else:
            return None

        self.cur.execute(f"SELECT * FROM LICENSE WHERE LICENSE_ID = '{license_id}'")
        rows = self.cur.fetchall()
        if len(rows) == 1:
            desc, name, price, lic_id = rows[0]
        else:
            return None

    def get_list_reports_for_period(self, start_date, end_date, est_name):
        est_id = self.get_id_est_by_name(est_name)
        self.cur = self.con.cursor()
        self.cur.execute(f"""SELECT baseinfo 
                             FROM public.report 
                             WHERE realdate BETWEEN '{start_date}' AND '{end_date}' AND establishment_id = {est_id}""")

        for r in self.cur.fetchall():
            print(r)

    def subscribe_user_to_est(self, telegram_id, est_name, pass_est):
        self.cur.execute(f"SELECT * FROM ESTABLISHMENTS WHERE \"NAME\" = '{est_name}'")
        rows = self.cur.fetchall()
        if len(rows) == 1:
            est_id, name, adress, passw, license_id, owner_id, report_type, path, date, extra = rows[0]
        else:
            return "Название не найдено"
        if passw != pass_est:
            return "Неправильный пароль"

        self.cur.execute(f"SELECT * FROM USERS WHERE TELEGRAM_ID = '{telegram_id}'")
        rows = self.cur.fetchall()
        if len(rows) == 1:
            user_id, name, login, role_id, passw, money, tg_id = rows[0]
        else:

            query = """
                            INSERT INTO USERS (TELEGRAM_ID, ROLE_ID) 
                            VALUES (%s, %s)
                        """
            self.cur.execute(query, (telegram_id, 5))
            self.con.commit()
            #дописать обработку возможной ошибки при добавлении в базу данных



            self.cur.execute(f"SELECT * FROM USERS WHERE TELEGRAM_ID = '{telegram_id}'")
            rows = self.cur.fetchall()
            if len(rows) == 1:
                user_id, name, login, role_id, passw_u, money, t_id = rows[0]

        self.cur.execute(f"SELECT * FROM SUBSCRIPTION WHERE USER_ID = '{user_id}' AND ESTABLISHMENTS_ID = '{est_id}'")
        rows = self.cur.fetchall()
        if(len(rows)):
            return "Вы уже подписаны"

        try:
            query = """
                        INSERT INTO SUBSCRIPTION ( USER_ID, ESTABLISHMENTS_ID) 
                    VALUES (%s, %s)
                    """
            self.cur.execute(query, (user_id, est_id))
            self.con.commit()
        except:
            return "Ошибка"

        LOGGER.info(str(datetime.now()) + f' Added user_id - {user_id} and est_id - {est_id} for telegram_id - {telegram_id}')
        return "success"

    def get_users_list_for_est(self, est_name ):
        self.cur.execute(f"SELECT * FROM establishments WHERE \"NAME\" = '{est_name}'")
        rows = self.cur.fetchall()
        if len(rows) == 1:
            id, name, adress, passw, license_id, owner_id, report_type, path, date, extra = rows[0]
        else:
            return "Название не найдено"

        self.cur.execute(f"SELECT * FROM SUBSCRIPTION WHERE ESTABLISHMENTS_ID = '{id}'")
        rows = self.cur.fetchall()
        users = []
        for row in rows:
            subsc_id, user_id, est_id = row
            users.append(user_id)
        return users

    def get_telegram_id(self, user_id):
        self.cur.execute(f"SELECT * FROM users WHERE user_id = '{user_id}'")
        rows = self.cur.fetchall()
        if len(rows) == 1:
            id, name, login, role_id, passw, money, tg_id = rows[0]
            return  tg_id
        else:
            return None

    def get_license_list(self):
        lic = []
        self.cur.execute(f"SELECT * FROM license")
        rows = self.cur.fetchall()
        for r in rows:
            id, name, license_id, owner_id = r
            lic.append(str(owner_id) + " " + name )

        return lic
    def get_full_license_list(self):
        self.cur.execute(f"SELECT * FROM license")
        rows = self.cur.fetchall()

        return rows

    def get_full_est_list(self):
        self.cur.execute(f"SELECT * FROM establishments")
        rows = self.cur.fetchall()

        return rows
    def get_role_list(self):
        lic = []
        self.cur.execute(f"SELECT * FROM public.\"ROLE\"")
        rows = self.cur.fetchall()
        for r in rows:
            id, name, desc = r
            lic.append(str(id) + " " + name)

        return lic

    def get_est_list_in_reports(self):
        est = {}
        self.cur.execute(f"SELECT * FROM REPORT")
        rows = self.cur.fetchall()
        for r in rows:
            id, name, adress, passw, license_id, owner_id = r
            #est append(str(owner_id) + " " + passw)

        return est

    def get_curent_servers_tasks_count(self, id):
        self.cur = self.con.cursor()
        self.cur.execute(f"SELECT COUNT(*) FROM TASKS WHERE SERVER_ID = {id} AND END_TIME IS NULL")
        return self.cur.fetchall()[0][0]

    def get_server_for_task(self, id_not_res = []):
        self.cur = self.con.cursor()
        self.cur.execute(f"SELECT * FROM SERVERS")
        rows = self.cur.fetchall()
        best_tasks = -1000
        ser_ip = ''
        ser_id = ''
        for r in rows:
            id, desc, ip, threads, dev = r

            if ip in id_not_res:
                continue
            if best_tasks < (threads - self.get_curent_servers_tasks_count(id)):
                best_tasks = threads - self.get_curent_servers_tasks_count(id)
                ser_ip = ip
                ser_id = id
                dev_id = dev

        return ser_ip, ser_id, dev_id

    def get_server_ip_by_id(self, id):
        self.cur = self.con.cursor()
        self.cur.execute(f"SELECT IP FROM SERVERS WHERE SERVER_ID = {id}")
        rows = self.cur.fetchall()
        if len(rows) == 1:
            return str(rows[0][0])
        else:
            return None

    def is_tg_user_owner(self, id):
        try:
            self.cur = self.con.cursor()
            user = self.cur.execute(f"SELECT USER_ID FROM USERS WHERE TELEGRAM_ID = {id}")
            user = user.fetchall()
            if len(user) == 0:
                return False
            user_id = user[0][0]
            self.cur = self.con.cursor()

            count = self.cur.execute(f"SELECT COUNT(*) FROM ESTABLISHMENTS WHERE OWNER_ID = {user_id}")
            count.fetchall()[0][0]

            if count == 0:
                return False
            else:
                return True
        except:
            return False
    def get_money_for_tg_user(self, id):
        count = 0
        try:
            self.cur = self.con.cursor()
            self.cur.execute(f"SELECT USER_ID FROM USERS WHERE TELEGRAM_ID = {id}")
            user = self.cur.fetchall()
            if len(user) == 0:
                return False
            user_id = user[0][0]
            self.cur = self.con.cursor()


            self.cur.execute(f"SELECT MONEY FROM USERS WHERE USER_ID = {user_id}")

            count = self.cur.fetchall()[0][0]
        except:
            pass
        return count

    def get_money_for_id_user(self, id):
        count = 0
        try:
            self.cur = self.con.cursor()
            self.cur.execute(f"SELECT USER_ID FROM USERS WHERE USER_ID = {id}")
            user = self.cur.fetchall()
            if len(user) == 0:
                return False
            user_id = user[0][0]
            self.cur = self.con.cursor()


            self.cur.execute(f"SELECT MONEY FROM USERS WHERE USER_ID = {user_id}")

            count = self.cur.fetchall()[0][0]
        except:
            pass
        return count

    def addmomey_for_tg_user(self, id, money):
        self.cur = self.con.cursor()
        self.cur.execute(f"SELECT user_id FROM users WHERE telegram_id = {id}")
        user = self.cur.fetchall()
        if len(user) == 0:
            return False
        user_id = user[0][0]
        self.cur = self.con.cursor()

        self.cur.execute(f"SELECT MONEY FROM USERS WHERE USER_ID = {user_id}")

        count = self.cur.fetchall()[0][0]

        self.cur = self.con.cursor()

        self.cur.execute(f"UPDATE USERS SET MONEY = {int(count + money)} WHERE USER_ID = {user_id}")
        self.con.commit()

        return True

    def get_est_list_for_tg_user(self, id):
        self.cur = self.con.cursor()
        self.cur.execute(f"SELECT USER_ID FROM USERS WHERE TELEGRAM_ID = {id}")
        user = self.cur.fetchall()
        if len(user) == 0:
            return None
        user_id = user[0][0]
        self.cur = self.con.cursor()
        self.cur.execute(f"SELECT ESTABLISHMENTS_ID FROM SUBSCRIPTION WHERE USER_ID = {user_id}")
        ests = self.cur.fetchall()
        names = []
        for est in ests:
            est = est[0]
            names.append(self.get_est_name_by_id(est))

        return names
    def get_est_name_by_id (self, id):
        self.cur = self.con.cursor()
        self.cur.execute(f"SELECT \"NAME\" FROM ESTABLISHMENTS WHERE ESTABLISHMENTS_ID = {id}")
        user = self.cur.fetchall()
        if len(user) == 0:
            return None
        return user[0][0]

    def get_est_name_by_owner_id(self, id):
        self.cur = self.con.cursor()
        self.cur.execute(f"SELECT USER_ID FROM USERS WHERE TELEGRAM_ID = {id}")
        user = self.cur.fetchall()
        if len(user) == 0:
            return None
        user_id = user[0][0]
        self.cur = self.con.cursor()
        self.cur.execute(f"SELECT \"NAME\" FROM ESTABLISHMENTS WHERE OWNER_ID = {user_id}")
        ests = self.cur.fetchall()
        names = []
        for est in ests:
            names.append(est[0])

        return names

    def get_license_name_and_price(self, lic_id):
        self.cur = self.con.cursor()
        self.cur.execute(f"SELECT \"NAME\", price FROM license WHERE license_id = {lic_id}")
        user = self.cur.fetchall()
        if len(user) == 0:
            return None
        lic_name = user[0][0]
        lic_price = user[0][1]
        return lic_name, lic_price

    def set_start_task(self, server_id, est_id, path):
        self.cur = self.con.cursor()
        insert_query = """
            INSERT INTO public.tasks (server_id, est_id, begin_time, "path")
            VALUES (%s, %s, %s, %s);
        """
        self.cur.execute(insert_query, (server_id, est_id, datetime.now().time(), path))
        self.con.commit()

    def set_end_task(self, server_id, est_id, path):
        delete_query = """
                    DELETE FROM public.tasks
                    WHERE server_id = %s
                    AND est_id = %s
                    AND "path" = %s
                    AND begin_time IS NOT NULL;
                """
        self.cur.execute(delete_query, (server_id, est_id, path))

        # Подтверждение транзакции
        self.con.commit()

    def db_set_date_license_expired(self, date, est_id):
        self.cur = self.con.cursor()
        update_query = f"""
        UPDATE public.establishments
        SET datelicense_expire = '{date}' 
        WHERE establishments_id = {est_id};
        """
        self.cur.execute(update_query)
        self.con.commit()

    def get_weights(self):
        self.cur = self.con.cursor()
        self.cur.execute("SELECT dbpath FROM public.settings WHERE setting_id = %s", (1,))
        row = self.cur.fetchone()

        if row:
            file_data = row[0]

            # Создание временного файла и запись в него данных
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                temp_file_name = temp_file.name
                temp_file.write(file_data.tobytes())
        os.rename(temp_file_name, temp_file_name + '.pt')
        return  temp_file_name + '.pt'

    def get_extra(self, est_name):
        self.cur.execute(f"SELECT  extra FROM ESTABLISHMENTS WHERE  \"NAME\" = '{est_name}'")
        extra = self.cur.fetchall()
        if len(extra) == 0:
            return None
        return extra[0][0]
def main():
    db = DB()

    out = ''
    #print(db.addmomey_for_tg_user('440385834', 100))
    #print(db.get_est_list_for_tg_user('440385834'))
    #print(db.get_money_for_tg_user('440385834'))
    #print(db.get_curent_servers_tasks_count(1))
    #print(db.subscribe_user_to_est('440385834', 'Pekarnya', 'Test'))

    #db.set_base_report('2023-08-06', 'Basic informat')
    #db.get_est_info_by_name('Pekarnya')
    #print(db.get_report_type('Pekarnya'))
    #print(db.get_license_list())
    #print(db.get_id_est_by_name('Pekarnya'))
    #print(db.get_users_list_for_est('Pekarnya'))
    #print(db.get_user_id_by_login('discens'))
    #print(db.get_telegram_id(0))
    #print(db.get_license_name_and_price(1))
    #print(db.get_server_for_task())
    #db.set_start_task("Test1", '1', '1', 'path1')
    #db.set_start_task("Test1", '1', '1', 'path2')
    #db.set_start_task("Test1", '1', '1', 'path3')
    #db.set_start_task("Test1", '1', '1', 'path4')
    #db.set_start_task("Test1", '1', '1', 'path5')
    print(db.get_server_for_task())
    #db.set_start_task("Test1", '1', '1', 'path6')

    #db.set_end_task("Test1", '1', '1', 'path')
    temp = db.get_weights()
    print(temp)
    os.remove(temp)


if __name__ == '__main__':
    main()