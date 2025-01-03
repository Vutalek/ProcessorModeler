from .Configure import Configure

# класс ОЗУ
# size отражает полный объём ОЗУ
# тем не менее текущий объём current_size
# всегда будет на os_size меньше из-за пространства, занимаемого операционной системой
# waiting_tasks - список задач, ожидающих выполнения
# running_tasks - список задач, выполняющихся в данный момент времени
# counter - счётчик номера задачи. Номер является идентификационным номером задачи в ОЗУ
class RAM:
    def __init__(self):
        pass

    # конфигурация
    def config(self):
        configure = Configure()
        conf = configure.RAM()
        self.size = conf["size"]
        self.current_size = conf["os_size"]
        self.os_size = conf["os_size"]
        self.waiting_tasks = []
        self.running_tasks = []
        self.counter = 0

    # возможна ли запись в ОЗУ
    def can_write(self, bytes):
        return (self.size - self.current_size) >= bytes
    
    # запись в ОЗУ, задача попадает в список задач, ожидающих выполнение
    def write(self, task):
        self.current_size += task.data
        self.waiting_tasks.append((self.counter, task))
        self.counter += 1

    # перевод задачи с номером index в состояние выполнения
    def run_task(self, index):
        ind = 0
        for i in range(len(self.waiting_tasks)):
            if self.waiting_tasks[i][0] == index:
                ind = i
                break
        task = self.waiting_tasks.pop(ind)
        self.running_tasks.append(task)

    # стирание задачи с номером index из ОЗУ после её выполнения
    def erase(self, index):
        ind = 0
        for i in range(len(self.running_tasks)):
            if self.running_tasks[i][0] == index:
                ind = i
                break
        self.current_size -= self.running_tasks[i][1].data
        self.running_tasks.pop(ind)

    # количество задач, ожидающих выполнения
    def in_wait(self):
        return len(self.waiting_tasks)
    
    # возвращает ожидающую задачу в порядке её поступления
    def head_task(self):
        return self.waiting_tasks[0]
    
    # проверка на пустоту ОЗУ (без учёта места, занимаемого ОС)
    def empty(self):
        return self.current_size == self.os_size

# класс-обёртка над списком для хранения задач. фактическим реализует очередь с ограниченным размером записей
# queue - список задач в формате (номер, задача)
# MAX_TASK - ограничение количества задач
class TaskQueue:
    def __init__(self, max):
        self.queue = []
        self.MAX_TASK = max

    # проверка, можно ли записать
    def can_append(self):
        return len(self.queue) < self.MAX_TASK

    # запись в очередь
    def append(self, task):
        self.queue.append(task)

    # чтение: возвращает элемент в начальной позиции
    def read(self):
        return self.queue.pop(0)
    
    # проверка на пустоту очереди
    def isempty(self):
        return len(self.queue) == 0
    
    # возвращает коэффициент заполнения очереди
    def fill_ratio(self):
        return len(self.queue)/self.MAX_TASK