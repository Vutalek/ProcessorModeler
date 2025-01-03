from .Configure import Configure
from .Ethernet import Ethernet
from threading import Thread
import time
from math import ceil

# линия передачи данных
# id - номер линии
# unit_delay - элементарная задержка времени
# throughput - пропускная способность
class Lane:
    def __init__(self, id):
        self.id = id
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
        conf = configure.PCIe()
        self.throughput = conf["throughput"]

    # присоединение получателя
    def connect_receiver(self, receiver):
        self.receiver = receiver

    # отправка кадра без задержки
    def undelayed_send(self, frame):
        self.receiver.receive(frame)

    # отправка кадра с задержкой
    def send(self, frame, time):
        self.delay(ceil(time / self.unit_delay))
        self.receiver.receive(frame)

# класс PCIe
# prefix - префикс, для задания префиксов формируемых потоков Ethernet
# lanes - список линий передачи
# channels - список каналов передачи (возможно аггрегированных)
# ethernet - формирователь потока Ethernet
class PCIe:
    def __init__(self, prefix):
        self.prefix = prefix

    # конфигурация
    def config(self):
        configure = Configure()
        conf = configure.PCIe()
        self.lanes = []
        for i in range(conf["lanes"]):
            self.lanes.append(Lane(i))
            self.lanes[i].config()
        self.channels = []
        self.ethernet = Ethernet(self.prefix)
        self.ethernet.config()

    # формирование потока
    # если параметр tasks пустой, или не указан, используется список задач из файла,
    # который был прочитал Ethernet
    def __streamify(self, tasks = []):
        if len(tasks) != 0:
            self.ethernet.set_tasks(tasks)
        return self.ethernet.construct_stream()

    # присоединение получателя к конкретной линии
    def connect_receiver(self, lane, receiver):
        self.lanes[lane].connect_receiver(receiver)

    # аггрегирование нескольких линий в одну логическую
    def create_channel(self, lanes_list):
        self.channels.append(lanes_list)

    # начало передачи данных
    # time_counter отражает общее время передачи данных
    # counter - счётчик отправленных кадров
    # batch - набор кадров для одновременной передачи
    def __start_transmission(self, channel_id, tasks, result):
        time_counter = 0
        channel = self.channels[channel_id]
        stream = self.__streamify(tasks)
        counter = 0
        batch = []
        for frame in stream:
            #tcp open connection
            if counter < 3:
                time_counter += self.__send_one_packet(channel[0], frame)
                counter += 1
                continue
            #data
            if counter < stream.length - 2:
                if len(batch) != len(channel):
                    batch.append(frame)
                    counter += 1
                if len(batch) == len(channel):
                    time_counter += self.__send_batch(channel, batch)
                    batch.clear()
                continue
            if len(batch) != 0:
                time_counter += self.__send_batch(channel, batch)
                batch.clear()
                continue
            #tcp close connection
            if counter >= stream.length - 2:
                time_counter += self.__send_one_packet(channel[0], frame)
                counter += 1
                continue
        result[0] = time_counter

    # параллельное начало передачи. Возвращает поток выполнения.
    def start_transmission(self, result, channel_id, tasks = []):
        t = Thread(target = self.__start_transmission, args = [channel_id, tasks, result])
        t.start()
        return t

    # отправка одного пакета по каналу
    def __send_one_packet(self, lane, frame):
        time = frame.bytes / self.lanes[lane].throughput + frame.IPG
        self.lanes[lane].send(frame, time)
        return time

    # отправка batch штук пакетов по каналу.
    def __send_batch(self, channel, frames):
        max_time = frames[0].bytes
        for frame in frames:
            if frame.bytes > max_time:
                max_time = frame.bytes
        time = max_time / self.lanes[0].throughput + frames[0].IPG
        for i in range(1, len(frames)):
            self.lanes[channel[i]].receiver.receive(frames[i])
        self.lanes[channel[0]].send(frames[0], time)
        return time