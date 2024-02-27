# main.py
from multiprocessing import Process
import os

def run_app1():
    os.system("python3 cards.py")

def run_app2():
    os.system("python3 abe.py")

if __name__ == "__main__":
    # Start cards.py
    p1 = Process(target=run_app1)
    p1.start()

    # Start abe.py
    p2 = Process(target=run_app2)
    p2.start()

    # Join processes
    p1.join()
    p2.join()
