import logging
import math
import re
import shutil
import sys
import time
from threading import Thread

from colorama import init, Fore
init(convert=True)

def similar(a, b):
    # return SequenceMatcher(None, a, b).ratio()
    score = 0
    for word in b.split():  # for every word in your string
        if word in a:  # if it is in your bigger string increase score
            score += 1
    return score

height = shutil.get_terminal_size().lines - 1
CSI = '\x1b['
CLEAR = CSI + '2J'
CLEAR_LINE = CSI + '2K'
SAVE_CURSOR = CSI + 's'
UNSAVE_CURSOR = CSI + 'u'
GOTO_INPUT = CSI + '%d;0H' % (height + 1)

def emit(*args):
    print(''.join(args))


def inputs():
    global do_exit
    while True:
        x = input("console >>")
        if x.lower() == "exit":
            do_exit = True
            return
        # print(f"Published: {x}")

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    a = "line1"
    b = "line2"
    c = "line3"
    #sys.stdout.write("\x1b]0;test1\x07")
    logging.info("test1")
    thread_a = Thread(target=inputs, daemon=False)
    thread_a.start()
    time.sleep(2)
    logging.info("test2")
    time.sleep(2)