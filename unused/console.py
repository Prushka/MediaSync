from time import sleep
from colorama import init, Fore
init(convert=True)
erase = '\x1b[1A\x1b[2K'

def download(number):
    print(erase + "File {} processed".format(number))

def completed(percent):
    print("({:1.1}% Completed)".format(percent))

if __name__ == '__main__':
    for i in range(1, 4):
        download(i)
        completed(i / 10)
        sleep(1)
