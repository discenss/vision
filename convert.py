import imageio_ffmpeg as ffmpeg
import numpy as np
import av

input_file = "input.mp4"
output_file = "output.mp4"



input_file = r"Z:\testipcam\MaxBeer\video\7minutes\10.59.58-11.07.00[R][0@0][0].mp4"
output_file = r"Z:\testipcam\MaxBeer\video\7minutes\test.mp4"

input_stream = av.open(input_file)
output_stream = av.open(output_file, 'w')

for packet in input_stream.demux():
    print(packet.stream.type)
    if packet.stream.type == 'video':
        frames = packet.decode()
        print('test')
        for frame in frames:
            frame = frame.reformat(format='yuv420p')
            frame = frame.reformat(format='cuda')  # Конвертирование в CUDA-формат
            output_stream.mux(frame.encode())
        output_stream.flush()

input_stream.close()
output_stream.close()