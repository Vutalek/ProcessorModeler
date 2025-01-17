from .Task import Task
from .Configure import Configure

# класс кадра данных Ethernet
# bytes - длина в байтах
# IPG - межкадровый интервал
# task_id - номер задачи
# islast - последний ли кадр в последовательности
# task - задача типа Task
class Frame:
    def __init__(self, bytes, ipg, t_id, islast, task = None):
        self.bytes = bytes
        self.IPG = ipg
        self.task_id = t_id
        self.islast = islast
        self.task = task

    # получение строкового представления кадра в следующем формате
    # байты,межкадровый_интервал,номер_задачи,последний_ли
    # если последний, то в строку добавится 
    # ,тип_задачи,цена_выполнения,объём_данных,время_жизни
    def __str__(self):
        string = f"{self.bytes},{self.IPG},{self.task_id},{self.islast}"
        if self.islast == 1:
            string += f",{self.task.type},{self.task.cost},{self.task.data},{self.task.ttl}"
        return string

# класс потока Ethernet.
# сам поток хранится во временном файле temp/stream{prefix}.txt
# length - количество кадров в потоке
class EthernetStream:
    def __init__(self, prefix):
        self.prefix = prefix
        file = open(f"temp/stream{prefix}.txt", "w")
        file.close()
        self.file = open(f"temp/stream{prefix}.txt", "r+")
        self.file.truncate(0)
        self.length = 0

    # закрытие работы с файлом
    def close_stream(self):
        self.file.close()

    # добавление n кадров в поток
    # так как поток будет содержать большое количество одинаковых кадров
    # то применяется автоматическое RLE кодирование последовательности
    # данные хранятся в виде
    # n,frame
    # frame задаётся его строковым представлением
    def append_frames(self, frame, n = 1):
        self.file.write(f"{n}," + str(frame) + "\n")
        self.length += n

    # проход по потоку
    def __iter__(self):
        self.current_frame = None
        self.current_n = 0
        self.file.seek(0)
        return self
    
    def __next__(self):
        if self.current_n == 0:
            line = self.file.readline()
            if line == "":
                raise StopIteration
            splitted = line.strip().split(",")
            self.current_n = int(splitted[0])
            bytes = int(splitted[1])
            ipg = float(splitted[2])
            t_id = int(splitted[3])
            islast = int(splitted[4])
            if islast == 1:
                type = splitted[5]
                cost = int(splitted[6])
                data = int(splitted[7])
                ttl = float(splitted[8])
                self.current_frame = Frame(bytes, ipg, t_id, islast, Task(type, cost, data, ttl))
            else:
                self.current_frame = Frame(bytes, ipg, t_id, islast)
        
        self.current_n -= 1
        return self.current_frame
    
    # количество кадров в потоке
    def __len__(self):
        return self.length

# формирователь Ethernet потока
# формирует потоки с префиксом {prefix}{counter}
# IPG - межкадровый интервал
# payload - максимальный размер пользовательских данных
# tasks - список задач, из которых формируется поток для передачи
class Ethernet:
    def __init__(self, prefix):
        self.prefix = prefix
        self.counter = 0

    # конфигурация
    def config(self):
        configure = Configure()
        conf = configure.Ethernet()
        self.IPG = conf["ipg"]
        self.payload = conf["payload"]
        self.tasks = []
        with open(conf["source"], "r") as file:
            for line in file:
                size, type, cost, ttl = line.split(",")
                self.tasks.append(Task(type, int(cost), int(size), float(ttl)/1000))

    # установка вручную списка заданий
    def set_tasks(self, tasks):
        self.tasks = tasks

    # непосредственное формирование потока кадров
    # формат кадра данных:
    # 1. 26 байт заголовка Ethernet (учитывается тэг)
    # 2. 20 байт заголовка IP
    # 3. 32 байта заголовка TCP (12 байт - опции)
    # 4. до payload-52 байта пользовательских данных
    # 5. 4 байта контрольная сумма
    # итого получим до payload-52 пользоватеьских данных, 52 байта метаданных, 30 байт метаданных Ethernet
    # после каждого кадра идёт межкадровый интервал временем IPG
    # В начале передачи происходит обмен 3 TCP-сообщениями для установления канала передачи
    # Далее происходит непосредственная передача данных
    # Далее происходит обмен 2 TCP-сообщениями для закрытия канала передачи
    def construct_stream(self):
        stream = EthernetStream(self.prefix + str(self.counter))
        self.counter += 1
        # tcp open connection
        stream.append_frames(Frame(82, self.IPG, -1, 1, Task("", 1, 1, 1)))
        stream.append_frames(Frame(82, self.IPG, -1, 1, Task("", 1, 1, 1)))
        stream.append_frames(Frame(82, self.IPG, -1, 1, Task("", 1, 1, 1)))
        # data
        for i in range(len(self.tasks)):
            n_packets = self.tasks[i].data // (self.payload - 52)
            if n_packets != 0:
                stream.append_frames(Frame(self.payload + 30, self.IPG, i, 0), n = n_packets)
            last_packet = self.tasks[i].data % (self.payload - 52)
            stream.append_frames(Frame(last_packet + 82, self.IPG, i, 1, self.tasks[i]))
        # tcp close connection
        stream.append_frames(Frame(82, self.IPG, -1, 1, Task("", 1, 1, 1)))
        stream.append_frames(Frame(82, self.IPG, -1, 1, Task("", 1, 1, 1)))
        return stream