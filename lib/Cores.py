from .Configure import Configure
from .Ethernet import Ethernet
from .Memory import TaskQueue
import time
import threading
import random
from math import ceil

# класс ядра
# id - номер ядра
# proc_id - номер процессора
# log - лог
# unit_delay - элементарная задержка времени
# frequency - тактовая частота
# OS_MAX_TASK - максимальное количество заданий в очереди исполнения
# task_q - локальная очередь задач
# ethernet - формирователь Ethernet потока
# mp_enable - флаг, обозначающий многопроцессорную архитектуру:
# ядру назначается канал и процессор для пересылки на него задачи.
# ratio - порог от 0 до 1 включения режима пересылки заданий
# если task_q заполнена на ratio процентов, то включается режим многопроцессорности
# и ядро может переслать задание привязанному к нему процессору
# data_threshold - порог объёма пользовательских данных в байтах, при котором выгоднее переслать задание, чем выполнить его самому
class Core(threading.Thread):
    def __init__(self, proc_id, id):
        threading.Thread.__init__(self)
        self.id = id
        self.proc_id = proc_id
        self.log = []
        t1 = time.time()
        for i in range(10):
            0 == 0
        t2 = time.time()
        self.unit_delay = (t2-t1)/10

    # создание задержки временем таким образом (выполнение n простейших операций с временем выполнения unit_delay)
    # позволяет эмулировать микросекундные задержки
    def delay(self, n):
        for i in range(n):
            0 == 0

    # конфигурация
    def config(self):
        configure = Configure()
        conf = configure.Core()
        self.frequency = conf["frequency"]
        self.OS_MAX_TASK = conf["os_max_task"]
        self.task_q = TaskQueue(conf["os_max_task"])
        self.ethernet = Ethernet(f"{self.proc_id}_{self.id}_")
        self.ethernet.config()
        self.mp_enable = False
        self.ratio = conf["ratio"]
        self.data_threshold = conf["data_threshold"]

    # подключение ОЗУ
    def connect_RAM(self, RAM):
        self.RAM = RAM

    # подключение PCIe
    def connect_PCIe(self, PCIe):
        self.PCIe = PCIe
    
    # подключение процессора для многопроцессорности
    def enable_mp(self, proc_channel, my_channel, queue_in, queue_out):
        self.proc = (proc_channel, my_channel, queue_in, queue_out)
        self.mp_enable = True

    # можно ли добавить задачу в очередь исполнения
    def can_append_task(self):
        return self.task_q.can_append()

    # добавление задачи в очередь исполнения
    def append_task(self, task):
        self.task_q.append(task)
    
    # запуска работы ядра
    # работает по принципу Round-Robin
    def run(self):
        self.working = True
        while self.working:
            self.work()

    # остановка работы ядра
    def stop(self):
        self.working = False
    
    # полезная работа:
    # если очередь пуста - пропуск
    # если не пуста:
    # если mp_enable = False, то задача выполняется
    # иначе, если коэффициент заполнения очереди больше или равен порогового и 
    # объём задачи больше или равен порогового, то задача пересылается
    # иначе, задача выполняется
    def work(self):
        if self.task_q.isempty():
            return
        else:
            if not self.mp_enable:
                task = self.task_q.read()
                self.__do_task(task)
            else:
                curr_ratio = self.task_q.fill_ratio()
                task = self.task_q.read()
                if curr_ratio >= self.ratio and task[1].data >= self.data_threshold:
                    self.__send_task(task)
                else:
                    self.__do_task(task)
            self.RAM.erase(task[0])

    # выполнение задания
    def __do_task(self, task):
        time_cost = task[1].cost / self.frequency
        self.delay(ceil(time_cost / self.unit_delay))
        self.log.append(f"Done {task[1].type} in {time_cost} seconds\n")   
    
    # пересылка задания на связанный процессор
    def __send_task(self, task):
        proc_channel, my_channel, q_in, q_out = self.proc
        q_in.put([0, proc_channel, [task[1]]])
        time_cost = 0
        while q_out.empty():
            continue
        time_cost = q_out.get()
        self.log.append(f"Sended {task[1].type} to connected processor in {time_cost} seconds\n")  
        
    # запись работы в файл logs/Core{proc_id}_{id}.txt
    def write_log(self):
        with open(f"logs/Core{self.proc_id}_{self.id}.txt", "w") as file:
            file.writelines(self.log)

# Класс-расширение класса Core
# представляет собой ядро, отвечающее за взаимодействие с вводом
# и за распределение заданий по ядрам своего процессора
# cores - ядра
class InputCore(Core):
    def __init__(self, proc_id, id):
        super().__init__(proc_id, id)
        self.cores = []

    # подключение ядра
    def append_core(self, core):
        self.cores.append(core)

    # приём кадра из входного потока
    def receive(self, frame):
        if frame.islast == 1:
            self.__reconstruct(frame)

    # сборка задачи из кадров и запись в ОЗУ, если это возможно
    def __reconstruct(self, last_frame):
        if last_frame.task_id == -1:
            return
        elif self.RAM.can_write(last_frame.task.data):
           self.RAM.write(last_frame.task)
           self.log.append(f"Received {last_frame.task.type}\n")
        else:
            self.log.append(f"Skipped {last_frame.task.type}\n")

    # полезная работа
    # если список задач, ожидающих выполнения, пуст - пропуск
    # иначе:
    # случайным образом выбрать свободной ядро и назначить ему задачу
    def work(self):
        if self.RAM.in_wait() == 0:
            return
        else:
            ind_core = random.randint(0, len(self.cores) - 1)
            core = self.cores[ind_core]
            while not core.can_append_task():
                ind_core = random.randint(0, len(self.cores) - 1)
                core = self.cores[ind_core]
            task = self.RAM.head_task()
            self.RAM.run_task(task[0])
            time_cost = 2 / self.frequency
            self.delay(ceil(time_cost / self.unit_delay))
            core.append_task(task)
            self.log.append(f"Sended {task[1].type} to {core.id} core in {time_cost} seconds\n")
            return