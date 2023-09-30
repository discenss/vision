# -*- coding: utf-8 -*-
#import fdb
import psycopg2
from psycopg2 import OperationalError
from datetime import datetime
from utils.general import LOGGER

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
                host="10.100.94.60",
                port="8080",
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

    def get_user_name_by_id(self, name):
        self.cur.execute(f"SELECT user_id FROM users WHERE \"NAME\" = '{name}'")
        rows = self.cur.fetchall()
        if len(rows) == 1:
            return str(rows[0][0])
        else:
            return None

    def get_report_type(self, name):
        self.cur.execute(f"SELECT * FROM ESTABLISHMENTS WHERE \"NAME\" = '{name}'")
        rows = self.cur.fetchall()
        if len(rows) == 1:
            id, name, adress, passw, license_id, owner_id, report_type, path, date = rows[0]
            return report_type
        else:
            return None

    def get_id_est_by_name(self, name):
        self.cur.execute(f"SELECT * FROM ESTABLISHMENTS WHERE \"NAME\" = '{name}'")
        rows = self.cur.fetchall()
        if len(rows) == 1:
            id, name, adress, passw, license_id, owner_id, report_type, path, date = rows[0]
            return id
        else:
            return None

    def set_base_report(self, est_name, realdate, baseinfo = None):

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

    def get_est_info_by_name(self, est_name):
        self.cur.execute(f'SELECT * FROM establishments WHERE "NAME" = \'{est_name}\'')
        rows = self.cur.fetchall()
        if len(rows) == 1:
            id, name, adress, passw, license_id, owner_id, report_type, path, date = rows[0]
        else:
            return None

        self.cur.execute(f"SELECT * FROM LICENSE WHERE LICENSE_ID = '{license_id}'")
        rows = self.cur.fetchall()
        if len(rows) == 1:
            desc, beg, end, name, price, lic_id = rows[0]
        else:
            return None

    def subscribe_user_to_est(self, telegram_id, est_name, pass_est):
        self.cur.execute(f"SELECT * FROM ESTABLISHMENTS WHERE \"NAME\" = '{est_name}'")
        rows = self.cur.fetchall()
        if len(rows) == 1:
            est_id, name, adress, passw, license_id, owner_id, report_type, path, date = rows[0]
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
            id, name, adress, passw, license_id, owner_id, report_type, path, date = rows[0]
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
            id, name, adress, passw, license_id, owner_id = r
            lic.append(str(owner_id) + " " + passw )

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
        servers = []
        best_tasks = 0
        ser_ip = ''
        for r in rows:
            id, desc, ip, threads = r

            if ip in id_not_res:
                continue
            if best_tasks < (threads - self.get_curent_servers_tasks_count(id)):
                best_tasks = threads - self.get_curent_servers_tasks_count(id)
                ser_ip = ip

        return ser_ip

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

def main():
    db = DB()

    out = ''
    print(db.addmomey_for_tg_user('440385834', 100))
    print(db.get_est_list_for_tg_user('440385834'))
    print(db.get_money_for_tg_user('440385834'))
    print(db.get_curent_servers_tasks_count(1))
    print(db.subscribe_user_to_est('440385834', 'Pekarnya', 'Test'))

    db.set_base_report('2023-08-06', 'Basic informat')
    db.get_est_info_by_name('Pekarnya')
    print(db.get_report_type('Pekarnya'))
    print(db.get_license_list())
    print(db.get_id_est_by_name('Pekarnya'))
    #print(db.get_users_list_for_est('Pekarnya'))
    #print(db.get_user_id_by_login('discens'))
    #print(db.get_telegram_id(0))

if __name__ == '__main__':
    main()