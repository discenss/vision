from multiprocessing.connection import Client
import os
import argparse
#from moviepy.editor import VideoFileClip, concatenate_videoclips


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    #parser.add_argument('--weights', nargs='+', type=str, default=ROOT / 'yolov5s.pt', help='model path or triton URL')
    parser.add_argument('--source', type=str, help='file/dir/FILE.MP4)')
    parser.add_argument('--project', type=str, help='file/dir/resultdir')
    parser.add_argument('--close', action='store_true', help='show results')
    parser.add_argument('--est', type=str, help='show results')
    parser.add_argument('--id', type=str, help='show results')
    parser.add_argument('--device', type=str, help='show results')
    args = parser.parse_args()

    address = ('10.100.94.60', 8443)
    conn = Client(address)


    if args.close is True:
        conn.send('close_server')
        exit(0)

    if args.project is None or os.path.isdir(args.project) == False:
        print('Dest project dir is not correct')
        conn.send('close')
        exit(-1)

    if os.path.isfile(args.source):
        conn.send('--source='+args.source + ' ' + '--project='+args.project + ' --est=' + args.est + ' --id=' +args.id + ' --device='+args.device)
    elif os.path.isdir(args.source):
        for f in os.listdir(args.source):
            if f.endswith(".MP4") or f.endswith('.mp4'):
                conn.send('--source=' + os.path.join(args.source, f) + ' ' + '--project=' + args.project)
    else:
        print('Source file is not correct')

    conn.send('close')
    conn.close()