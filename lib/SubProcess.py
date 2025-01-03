import multiprocessing as mp
from threading import Thread
import time

from .Processor import Processor
from .Configure import Configure

# класс для запуска раоты проецссора в отдельном процессе
# proc - процессор
# profile - профиль настройки каналов
# queue_in - входящая очередь сообщений для межпроцессного взаимодействия
# queue_out - исходящая очередь сообщений для межпроцессного взаимодействия
# thread_work - работа потока приёма сообщений и их обработки из очереди сообщений
class SubProcess(mp.Process):
    def __init__(self, profile, id, q_in, q_out):
        mp.Process.__init__(self)
        self.proc = Processor(id)
        self.profile = profile
        self.queue_in = q_in
        self.queue_out = q_out
        self.thread_work = True

    # программа процесса
    # 1. запуск потока обработки очереди сообщений
    # 2. конфигурация и запуск процессора
    # 3. ожидание завершения работы
    def run(self):
        t = Thread(target = self.thread_job)
        t.start()

        self.proc.config(self.profile)

        self.proc.run()

        t.join()

    # обработка входящей очереди сообщений
    # парсит входящие объекты как команды
    # команда: [номер_команды, аргументы...]
    # команды:
    # команда 0:
    # начало передачи заданий
    # аргументы:
    # канал
    # список передаваемых заданий
    #
    # команда 1:
    # завершение работы процессора и процесса
    def thread_job(self):
        time.sleep(1)
        while self.thread_work:
            if self.queue_in.empty():
                continue
            else:
                comm = self.queue_in.get()
                if comm[0] == 0:
                    self.start_transmission(comm[1], comm[2])
                elif comm[0] == 1:
                    self.shutdown()

    # начало передачи
    # по завершение передачи записывает time_cost в исходящую очередь
    def start_transmission(self, channel, tasks = []):
        time_cost = self.proc.start_transmission(channel, tasks)
        self.queue_out.put(time_cost)

    # завершение работы процессора и процесса
    def shutdown(self):
        self.proc.stop()
        self.proc.write_logs()
        self.thread_work = False