# This is a sample Python script.

# Press ⌃R to execute it or replace it with your code.
# Press Double ⇧ to search everywhere for classes, files, tool windows, actions, and settings.
import io
import os
import codecs
import chardet
import xml.etree.ElementTree as ET
import os
import time
import datetime
import json
from db import DB
from utils.general import LOGGER

#from moviepy.editor import VideoFileClip, concatenate_videoclips
#from moviepy.video.io.VideoFileClip import VideoFileClip
#from moviepy.video.VideoClip import ImageClip

import cv2
FPS = 10.00
HOURS_DIFFERENCE = 8

class Event :
    def __init__(self):
        self.begin = 0
        self.end = 0
        self.type = 0

    def __init__(self, b, e, t):
        self.begin = b
        self.end = e
        self.type = t

events = []
bookmarks = []

BARCOUNTER = 0
PERSON = 1
COFFEE = 2
OPENEDCASH = 3
PACK = 4
TERMINAL = 5

OPENEDCASH_NO_CLIENT = 0
NO_WORKERS = 1
OPENEDCASH_CLIENT = 2

class OpenedCashNoClient:
    MINLENGHT = 6 * 10
    TRSHLD = 10  * 4

    def __init__(self):
        self.lst = []
        self.treshhold = 0
        self.lght = 0
        self.first = 0
        self.last = 0
        self.items = []

    def check(self, frame):
        if frame.opened_cash_noclient():
            if self.lght == 0: self.first = frame.num
            self.lght = self.lght + 1
            self.last = frame.num
            self.treshhold = 0
        elif self.lght > 0 and self.treshhold < self.TRSHLD:
            self.lght += 1
            self.treshhold += 1
            self.last = frame.num
        elif self.treshhold >= self.TRSHLD:
            if self.lght > self.MINLENGHT:
                #self.items.append({'begin': self.first, 'end': self.last})
                events.append(Event(self.first, self.last, OPENEDCASH_NO_CLIENT))
                self.last = 0
                self.first = 0
            self.lght = 0
            self.treshhold = 0

    def close(self):
        if self.lght > self.MINLENGHT:
            #self.items.append({'begin': self.first, 'end': self.last})
            events.append(Event(self.first, self.last, OPENEDCASH_NO_CLIENT))

class OpenedCash:
    MINLENGHT = 3 * 10
    TRSHLD = 10 * 5

    def __init__(self):
        self.lst = []
        self.treshhold = 0
        self.lght = 0
        self.first = 0
        self.last = 0
        self.items = []

    def check(self, frame):
        if frame.is_opened_cash():
            if self.lght == 0: self.first = frame.num
            self.lght = self.lght + 1
            self.last = frame.num
            self.treshhold = 0

        elif self.lght > 0 and self.treshhold < self.TRSHLD:
            self.treshhold += 1
            self.last = frame.num
        elif self.treshhold >= self.TRSHLD:
            if self.lght > self.MINLENGHT:
                #self.items.append({'begin': self.first, 'end': self.last})
                events.append(Event(self.first, self.last, OPENEDCASH_CLIENT))
                self.last = 0
                self.first = 0
            self.lght = 0
            self.treshhold = 0

    def close(self):
        if self.lght > self.MINLENGHT:
            #self.items.append({'begin': self.first, 'end': self.last})
            events.append(Event(self.first, self.last, OPENEDCASH_NO_CLIENT))

class NoWorkers:
    MINLENGHT = 300 * 10
    TRSHLD = 1 * 10

    def __init__(self):
        self.lst = []
        self.treshhold = 0
        self.lght = 0
        self.first = 0
        self.last = 0
        self.items = []

    def check(self, frame):
        if frame.is_person() is False:
            if self.lght == 0: self.first = frame.num
            self.lght = self.lght + 1
            self.last = frame.num
            self.treshhold = 0
        elif self.lght > 0 and self.treshhold < self.TRSHLD:
            self.lght += 1
            self.treshhold += 1
            self.last = frame.num
        elif self.treshhold >= self.TRSHLD:
            if self.lght > self.MINLENGHT:
                self.items.append({'begin': self.first, 'end': self.last})
                #events.append(Event(self.first, self.last, NO_WORKERS))
                self.last = 0
                self.first = 0
            self.lght = 0
            self.treshhold = 0

    def close(self):
        if self.lght > self.MINLENGHT:
            self.items.append({'begin': self.first, 'end': self.last})
            #events.append(Event(self.first, self.last, NO_WORKERS))


class CustQueue:
    MINLENGHT = 5 * 25
    TRSHLD = 15

    def __init__(self):
        self.lst = []
        self.treshhold = 0
        self.lght = 0
        self.first = 0
        self.last = 0
        self.items = []

    def check(self, frame):
        if frame.is_custumer_queue():
            if self.lght == 0: self.first = frame.num
            self.lght = self.lght + 1
            self.last = frame.num
        elif self.lght > 0 and self.treshhold < self.TRSHLD:
            self.lght += 1
            self.treshhold += 1
            self.last = frame.num
        elif self.treshhold >= self.TRSHLD:
            if self.lght > self.MINLENGHT:
                self.items.append({'begin': self.first, 'end': self.last})
                self.last = 0
                self.first = 0
            self.lght = 0
            self.treshhold = 0

    def close(self):
        if self.lght > self.MINLENGHT:
            self.items.append({'begin': self.first, 'end': self.last})


class Object:
    def __init__(self, t, xc, yc, xsc, ysc):
        self.type = t
        self.x = xc
        self.y = yc
        self.xs = xsc
        self.ys = ysc


class Frame:

    def add_object(self, obj):
        self.objects.append(obj)

    def __init__(self, f):
        self.objects = []
        self.num = f

    def opened_cash_noclient(self):
        cash = next(filter(lambda o: o.type == OPENEDCASH, self.objects), None)
        if cash is None:
            return False
        else:#Проверяем нет ли людей по координате Y. Если их нет, то значит касса открыта когда нет людей
            result = next(filter(lambda o: (o.type == PERSON and o.y < cash.y), self.objects), None)
            if result is None:
                return True
            else:
                return False

    def is_opened_cash(self):
        cash = next(filter(lambda o: o.type == OPENEDCASH, self.objects), None)
        if cash is None:
            return False
        else:
            return True

    def is_custumer_queue(self):
        cash_mashine = next(filter(lambda o: o.type == BARCOUNTER, self.objects), None)
        if cash_mashine is None:
            return False

        clients = list(filter(lambda o: (o.type == PERSON), self.objects))

        if len(clients) > 4:
            return True
        else:
            return False

    def is_person(self):
        person = next(filter(lambda o: o.type == PERSON, self.objects), None)
        if person is None:
            return False
        else:
            return True


def parse_result(path):
    frames = []
    with open(path, "rb") as f:
        bytes = min(32, os.path.getsize(path))
        raw = f.read(bytes)
        if raw.startswith(codecs.BOM_UTF8):
            encoding = 'utf-8-sig'
        else:
            result = chardet.detect(raw)
            encoding = result['encoding']

        infile = io.open(path, 'r', encoding=encoding)
        data = infile.read()
        infile.close()

        frame = Frame(1)
        for l in data.split('\n'):
            if l.startswith('Frame__'):
                if int(l[7:]) > 1:
                    frames.append(frame)
                    frame = Frame(int(l[7:]))
            elif len(l) > (len('----')):
                par = l.split(' ')
                frame.add_object(Object(int(par[0]), float(par[1]), float(par[2]), float(par[3]), float(par[4])))

        infile = io.open(path, 'r', encoding=encoding)
        data = infile.read()
        infile.close()

    return frames

def get_time_for_frames(frame, hours_difference):

    h = int(frame // (3600 * FPS)) + hours_difference
    m = int((frame % (3600 * FPS)) // (FPS * 60))
    s = int(((frame % (3600 * FPS))) % (FPS * 60) / FPS)

    return datetime.time(hour=h, minute=m, second=s)


def parse_aiko(pay_report):
    orders = []#time when report was closed, FALSE - card, TRUE - cash// FALSE - not proceed, TRUE - proceed
    #pay_report = video_file[:-3] + "json"
    if os.path.isfile(pay_report):
        with open(pay_report, 'r', encoding='utf-8') as f:
            data = json.load(f, encoding='utf-8')
            for client in data['orders']:
                if (client['order']['payments'] != None and client['order']['payments'][0]['paymentType']['kind'] == 'External'): #card
                    if client['order']['whenClosed'] != None:
                        datetime_obj = datetime.datetime.strptime(client['order']['whenClosed'], "%Y-%m-%d %H:%M:%S.%f")
                        orders.append([datetime_obj.time(), False, False])
                else:#cash
                    if client['order']['whenClosed'] != None:
                        datetime_obj = datetime.datetime.strptime(client['order']['whenClosed'], "%Y-%m-%d %H:%M:%S.%f")
                        orders.append([datetime_obj.time(), True, False])

    else:
        LOGGER.info(str(datetime.datetime.now()) + f' File not found: {pay_report}')

    return orders

def parse_poster(pay_report):
    orders = []
    if os.path.isfile(pay_report):
        with open(pay_report, 'r', encoding='utf-8') as f:
            data = json.load(f, encoding='utf-8')
            for num, client in data.items():
                if ('cash' in client['payments']):  # card
                    if client['close'] != None:
                        datetime_obj = datetime.datetime.strptime(client['close'], "%Y-%m-%d %H:%M:%S")
                        t = datetime_obj.time()
                        orders.append([t, True, False])
                else:
                    if client['close'] != None:
                        datetime_obj = datetime.datetime.strptime(client['close'], "%Y-%m-%d %H:%M:%S")
                        t = datetime_obj.time()
                        orders.append([t, False, False])
    else:
        LOGGER.info(str(datetime.datetime.now()) + f' File not found: {pay_report}')

    return orders

def create_report(file_path, orders, result, hours_difference):

    if os.path.isfile(file_path):
        frames = parse_result(file_path)
    else:
        return None
    text_report = []
    cust_queue = CustQueue()
    no_workers = NoWorkers()
    opened_cash = OpenedCash()
    for f in frames:
        no_workers.check(f)
        opened_cash.check(f)

    cust_queue.close()
    no_workers.close()
    opened_cash.close()

    for e in events:
        text = ''

        if e.type == NO_WORKERS:
            text = "No_workers"

        elif e.type == OPENEDCASH_CLIENT:
            time_begin = get_time_for_frames(e.begin, hours_difference)
            time_end = get_time_for_frames(e.end, hours_difference)
            sell = ''
            for order in orders:
                if order[1] == True:
                    time_sell = order[0]

                    time_begin_seconds = time_begin.hour * 3600 + time_begin.minute * 60 + time_begin.second
                    time_end_seconds = time_end.hour * 3600 + time_end.minute * 60 + time_end.second
                    time_sell_seconds = time_sell.hour * 3600 + time_sell.minute * 60 + time_sell.second

                    diff_begin = time_begin_seconds - time_sell_seconds
                    diff_end = time_end_seconds - time_sell_seconds

                    if time_sell > time_begin and time_sell < time_end  or abs(diff_begin) < 60 or abs(diff_end) < 60:
                        sell = ' Cash '
                        order[2] = True
                        break

            text = "Opened cash: " + str(time_begin) + " " + sell

        #result = text + " begin: " + str(e.begin) + " end: " + str(e.end)
        bookmarks.append((int(e.begin/FPS), text))

    for order in orders:
        time_sell = order[0]
        time_sell = (time_sell.hour - hours_difference) * 3600 + time_sell.minute * 60 + time_sell.second

        if order[1] == False:
            bookmarks.append((int(time_sell), 'Pay card: ' + str(order[0])[:-6]))
            order[2] = True
        else:
            if order[2] == False:
                bookmarks.append((int(time_sell), 'WARNING. Cash : ' + str(order[0])[:-6]))
                order[2] = True

    if len(no_workers.items) > 2:

        if (no_workers.items[0]['begin'] / len(frames) < 0.01):
            bookmarks.append((int(no_workers.items[0]['end'] / FPS),
                      'Opening: ' + str(get_time_for_frames(no_workers.items[0]['begin'], hours_difference))))
            text_report.append(u'🔓Открытие: ' + str(get_time_for_frames(no_workers.items[0]['end'], hours_difference)))
            no_workers.items.remove(no_workers.items[0])
        else:
            bookmarks.append(( 0,
                              'Already opened in begin. Opening: ' + str(get_time_for_frames(0, hours_difference))))
            text_report.append(u'🔓Уже открыто: ' + str(get_time_for_frames(0, hours_difference)))

        if ((len(frames) - no_workers.items[-1]['end']) / len(frames) < 0.01):
            bookmarks.append((int(no_workers.items[-1]['begin'] / FPS),
                              'Closing: ' + str(get_time_for_frames(no_workers.items[-1]['begin'], hours_difference))))
            text_report.append('🔓Закрыто: ' + str(get_time_for_frames(no_workers.items[-1]['begin'], hours_difference)))
            no_workers.items.remove(no_workers.items[-1])
        else:
            bookmarks.append((0,
                              u'Ещё не закрыто в : ' + str(get_time_for_frames(len(frames), hours_difference))))
            text_report.append(u'🔓Ещё не закрыто в : ' + str(get_time_for_frames(len(frames), hours_difference)))
        text_report.append("🧍‍♂️ Нет на рабочем месте:\n")

        total_time = 0
        for e in no_workers.items[0:-1]:
            bookmarks.append((int(e['begin'] / FPS),
                          'No workers: ' + str(get_time_for_frames(e['begin'], hours_difference))))
            time1 = get_time_for_frames(e['begin'], hours_difference)
            time2 = get_time_for_frames(e['end'], hours_difference)
            total_time += (time2.hour - time1.hour)*60 + (time2.minute - time1.minute)
            text_report.append(f" c {str(get_time_for_frames(e['begin'], hours_difference))} по {str(get_time_for_frames(e['end'], hours_difference))}")

        text_report.append(f'🧍‍♂️Общее время отсутствия: { total_time} мин')

    else:
        bookmarks.append((0,
                          'Already opened in ' + str(get_time_for_frames(0, hours_difference))))
        text_report.append(u'🔓Уже открыто: ' + str(get_time_for_frames(0, hours_difference)))
        text_report.append(u' Не замечено отсутствие на рабочем месте')
        bookmarks.append((0,
                          u'Still working at : ' + str(get_time_for_frames(len(frames, hours_difference)))))
        text_report.append(u'🔓Ещё не закрыто в : ' + str(get_time_for_frames(len(frames, hours_difference))))

    begin = 0
    midle = 0
    end = 0
    for o in orders:
        if o[0].hour < 13:
            begin = begin + 1
        elif o[0].hour >= 13 and o[0].hour < 19:
            midle = midle + 1
        elif o[0].hour >= 19:
            end = end + 1

    text_report.append("📉Уровень загрузки проекта:\n")
    text_report.append(f"8:00 - 13:00 : {begin}\n")
    text_report.append(f"13:00 - 19:00 : {midle}\n")
    text_report.append(f"19:00 - 22:00 : {end}\n")

    media_file = os.path.basename(result)[:-4] + "mp4"
    root = ET.Element("playlist", version="1", xmlns="http://www.videolan.org/vlc/playlist/ns/0/")
    track_list = ET.SubElement(root, "trackList")

    for timestamp, description in bookmarks:
        track = ET.SubElement(track_list, "track")
        location = ET.SubElement(track, "location")
        location.text = f"{media_file}"
        title = ET.SubElement(track, "title")
        title.text = description
        extension = ET.SubElement(track, 'extension', application="http://www.videolan.org/vlc/playlist/0")
        option = ET.SubElement(extension, 'vlc:option')
        option.text = "start-time=" + str(timestamp)

    tree = ET.ElementTree(root)

    tree.write(result, encoding="utf-8", xml_declaration=True)
    return text_report

def parse_report(report_file, est_name):
    db = DB()
    orders = []
    report_type = db.get_report_type(est_name)
    if report_type == "aiko":
        orders = parse_aiko(report_file)
    elif report_type == "poster":
        orders = parse_poster(report_file)

    return orders

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    video_file =  r'Z:\testipcam\MaxBeer\video\1280\3_2023-09-12_11-00-00.mp4'
    report_file = video_file [:-4] + ".json"
    orders = parse_poster(report_file)
    #db = DB()
    frames_file = r'E:\dev\sources\testing\exp75\labels\2_2023-08-19_08-00-00.txt'

    text_base_report = create_report(frames_file, orders, video_file[:-4] + '.xspf', 8)
    print(text_base_report)
    #result = '\n'.join(text_base_report)
    #db.set_base_report('Pekarnya', '2023-08-05', result)
    #print(result)
    #create_xspf_playlist('2_2023-07-12_08-00-00.mp4', bookmarks, "2_2023-07-12_08-00-00.xspf")
    #frames_file = r"E:\dev\sources\testing\exp25\labels\3_2023-08-13_11-00-00.txt"
    #orders = parse_poster(r"Z:\testipcam\MaxBeer\video\1280\3_2023-08-13_11-00-00.json")
    #print(create_report(frames_file, orders, r"E:\dev\sources\testing\exp25\3_2023-08-13_11-00-00.xspf"))

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
