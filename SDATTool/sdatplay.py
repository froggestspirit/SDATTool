#!/usr/bin/python3
import pyaudio
import ctypes
import os

MIXER_FREQ = 24000
workingDir = f"{os.getcwd()}/"
libsdatplay = ctypes.CDLL(f"{workingDir}libsdatplay.so", mode=ctypes.RTLD_GLOBAL|os.RTLD_LAZY)

player = {"p": None, "stream": None}


def callback(in_data, frame_count, time_info, status):
    data = bytearray(frame_count*8)
    for i in range(frame_count):
        out = libsdatplay.RunMixerFrame()[0].to_bytes(8, 'little')
        data[(i*8):(i*8)+8] = out
    return (bytes(data), pyaudio.paContinue)

def init():
    libsdatplay.sdatplay_init.restype = ctypes.POINTER(ctypes.c_uint32)
    libsdatplay.RunMixerFrame.restype = ctypes.POINTER(ctypes.c_uint64)
    player["p"] = pyaudio.PyAudio()


def play(infoblock, index):
    try:
        player["stream"].stop_stream()
        player["stream"].close()
    except AttributeError:
        pass
    sdatplay = libsdatplay.sdatplay_init(ctypes.c_uint32(MIXER_FREQ))
    libsdatplay.load_sseq(ctypes.c_char_p(f"{infoblock.folder}/{infoblock.seq.records[index].file_id}".encode('UTF-8')))
    bank_name = infoblock.seq.records[index].bnk
    bank_id = list(i.symbol for i in infoblock.bank.records).index(bank_name)
    for i, inst in enumerate(infoblock.sbnk_data[bank_id].data):
        if inst:
            libsdatplay.set_inst_type(ctypes.c_uint32(i), ctypes.c_uint32(inst["type"]))
            if inst["type"] == 16:  # range
                key = inst["range_low"]
                for swav_parms in inst["data"]:
                    if isinstance(swav_parms.swav, str):
                        swav_arg = ctypes.c_char_p(f"{infoblock.folder}/SWAR/{swav_parms.swav}".encode('UTF-8'))
                    else:
                        swav_arg = ctypes.c_char_p(f"{swav_parms.swav}".encode('UTF-8'))
                    libsdatplay.set_inst(ctypes.c_uint32(i), ctypes.c_uint32(key), swav_arg, ctypes.c_uint32(swav_parms.note), ctypes.c_uint32(swav_parms.attack), ctypes.c_uint32(swav_parms.decay), ctypes.c_uint32(swav_parms.sustain), ctypes.c_uint32(swav_parms.release), ctypes.c_uint32(swav_parms.pan))
                    key += 1
            elif inst["type"] == 17:  # keysplit
                split = 0
                key_low = 0
                for swav_parms in inst["data"]:
                    if inst["keysplits"][split]:
                        key_high = inst["keysplits"][split]
                        split += 1
                        if isinstance(swav_parms.swav, str):
                            swav_arg = ctypes.c_char_p(f"{infoblock.folder}/SWAR/{swav_parms.swav}".encode('UTF-8'))
                        else:
                            swav_arg = ctypes.c_char_p(f"{swav_parms.swav}".encode('UTF-8'))
                        libsdatplay.set_inst_range(ctypes.c_uint32(i), ctypes.c_uint32(key_low), ctypes.c_uint32(key_high), swav_arg, ctypes.c_uint32(swav_parms.note), ctypes.c_uint32(swav_parms.attack), ctypes.c_uint32(swav_parms.decay), ctypes.c_uint32(swav_parms.sustain), ctypes.c_uint32(swav_parms.release), ctypes.c_uint32(swav_parms.pan))
                        key_low = key_high + 1
            else:
                swav_parms = inst["data"][0]
                if isinstance(swav_parms.swav, str):
                    swav_arg = ctypes.c_char_p(f"{infoblock.folder}/SWAR/{swav_parms.swav}".encode('UTF-8'))
                else:
                    swav_arg = ctypes.c_char_p(f"{swav_parms.swav}".encode('UTF-8'))
                libsdatplay.set_inst(ctypes.c_uint32(i), ctypes.c_uint32(0), swav_arg, ctypes.c_uint32(swav_parms.note), ctypes.c_uint32(swav_parms.attack), ctypes.c_uint32(swav_parms.decay), ctypes.c_uint32(swav_parms.sustain), ctypes.c_uint32(swav_parms.release), ctypes.c_uint32(swav_parms.pan))
    if not sdatplay:
        print('Error initializing sdatplay')
        quit()

    # open stream using callback (3)
    player["stream"] = player["p"].open(format=pyaudio.paFloat32,
                    channels=2,
                    rate=MIXER_FREQ,
                    output=True,
                    stream_callback=callback)
    # start the stream (4)
    player["stream"].start_stream()

    # wait for stream to finish (5)
    #while player["stream"].is_active():
    #    pass

def stop():
    # stop stream (6)
    player["stream"].stop_stream()
    player["stream"].close()

    # close PyAudio (7)
    player["p"].terminate()