from lib.SubProcess import SubProcess
from lib.Processor import Processor
import multiprocessing as mp
import time
import datetime

if __name__ == "__main__":
    tg_1 = time.time()

    print(datetime.datetime.now().strftime("%H:%M:%S") + " Creating and starting processors...")
    sp1_in = mp.Queue()
    sp1_out = mp.Queue()
    sp1 = SubProcess("slave", 1, sp1_in, sp1_out)

    sp2_in = mp.Queue()
    sp2_out = mp.Queue()
    sp2 = SubProcess("slave", 2, sp2_in, sp2_out)

    sp3_in = mp.Queue()
    sp3_out = mp.Queue()
    sp3 = SubProcess("slave", 3, sp3_in, sp3_out)

    main = Processor(0)
    main.config("master")
    main.append_proc(1, 0, 1, sp1_in, sp1_out)
    main.append_proc(2, 0, 2, sp2_in, sp2_out)
    main.append_proc(3, 0, 3, sp3_in, sp3_out)

    main.run()
    sp1.start()
    sp2.start()
    sp3.start()
    time.sleep(5)

    print(datetime.datetime.now().strftime("%H:%M:%S") + " Starting transmission...")
    t1 = time.time()
    main.start_transmission(0)
    t2 = time.time()
    print(datetime.datetime.now().strftime("%H:%M:%S") + " Waiting until processors done all their work...")
    main.stop()

    tg_2 = time.time()

    print(datetime.datetime.now().strftime("%H:%M:%S") + f" Transmission time: {t2-t1} seconds")
    print(datetime.datetime.now().strftime("%H:%M:%S") + f" Script execution time: {tg_2 - tg_1} seconds")
    main.write_logs()
    with open("logs/General.txt", "w") as file:
        file.write(f"Transmission time: {t2-t1} seconds.\n")
        file.write(f"Script execution time: {tg_2 - tg_1} seconds.\n")