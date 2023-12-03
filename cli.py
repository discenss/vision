from multiprocessing.connection import Client
import os
import argparse
#from moviepy.editor import VideoFileClip, concatenate_videoclips


import argparse
import os
from multiprocessing.connection import Client

def read_config(file_name):
    config = {}
    with open(file_name, 'r') as file:
        for line in file:
            key, value = line.strip().split(' & ')
            config[key] = value
    return config

if __name__ == '__main__':
    config = read_config('serv.cfg')
    ip = config.get('ip', '127.0.0.1')
    port = int(config.get('port', 8443))

    parser = argparse.ArgumentParser()
    parser.add_argument('--source', type=str, help='file/dir/FILE.MP4)')
    parser.add_argument('--project', type=str, help='file/dir/resultdir')
    parser.add_argument('--close', action='store_true', help='close server')
    parser.add_argument('--est', type=str, help='est id')
    parser.add_argument('--id', type=str, help='server id')
    parser.add_argument('--device', type=str, default='0', help='device id')
    parser.add_argument('--debug', default=False, action='store_true', help='debugging mode')

    args = parser.parse_args()

    address = (ip, port)
    conn = Client(address)

    if args.close:
        conn.send('close_server')
        conn.close()
        exit(0)

    if args.source is None:
        print('Source is not specified')
        conn.send('close')
        conn.close()
        exit(-1)

    command_parts = []

    if os.path.isfile(args.source):
        command_parts.append('--source=' + args.source)
    else:
        print('Source file is not correct')
        conn.send('close')
        conn.close()
        exit(-1)

    if args.project:
        command_parts.append('--project=' + args.project)

    if args.est:
        command_parts.append('--est=' + args.est)
    if args.id:
        command_parts.append('--id=' + args.id)
    if args.device:
        command_parts.append('--device=' + args.device)
    if args.debug:
        command_parts.append('--debug')

    command = ' '.join(command_parts)
    conn.send(command)

    conn.send('close')
    conn.close()
