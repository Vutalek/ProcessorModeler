from .Configure import Configure
from .Cores import Core, InputCore
from .PCIe import PCIe
from .Memory import RAM
from multiprocessing import Queue

# класс процессора
# id - номер процессора
# slaves - список привязанных процессоров в формате (канал присоединённого процессора, свой канал, входящая очередь процессора, исходящая очередь процессора)
# cores - список ядер, 0 ядро - всегда ядро-планировщик 
# RAM - объект ОЗУ
# PCIe - объект PCIe
class Processor:
    def __init__(self, id):
        self.id = id
        self.slaves = []

    # конфигурация
    def config(self, profile):
        configure = Configure()
        conf = configure.Processor()
        cores = conf["number_of_cores"]

        self.cores = [InputCore(self.id, 0)]
        for i in range(1, cores):
            c = Core(self.id, i)
            self.cores.append(c)
            self.cores[0].append_core(c)
        for core in self.cores:
            core.config()

        self.RAM = RAM()
        self.RAM.config()
        for core in self.cores:
            core.connect_RAM(self.RAM)

        self.PCIe = PCIe(f"{self.id}_")
        self.PCIe.config()
        for i in range(len(self.PCIe.lanes)):
            self.PCIe.connect_receiver(lane = i, receiver = self.cores[0])
        for core in self.cores:
            core.connect_PCIe(self.PCIe)

        channels = configure.ProcChannels(profile)
        for chnl in channels:
            self.create_channel(chnl)

    # соаздание канала в PCIe
    def create_channel(self, lanes):
        self.PCIe.create_channel(lanes)

    # Присоединение процессора и выбор связанного ядра
    def append_proc(self, core, proc_channel, my_channel, queue_in, queue_out):
        self.slaves.append((proc_channel, my_channel, queue_in, queue_out))
        self.cores[core].enable_mp(proc_channel, my_channel, queue_in, queue_out)

    # запуск работы процессора
    def run(self):
        for core in self.cores:
            core.start()

    # остановка процессора
    def stop(self):
        while not self.RAM.empty():
            continue

        for core in self.cores:
            core.stop()

        for core in self.cores:
            core.join()

        for pc, mc, q_in, q_out in self.slaves:
            q_in.put([1])

    # начало передачи К(!!!) этому процессору
    # channel - номер канала передачи внутри процессора приёмника (этого процессора)
    def start_transmission(self, channel, tasks = []):
        out = [0]
        t = self.PCIe.start_transmission(out, channel, tasks = tasks)
        t.join()
        return out[0]

    # запись логов работы ядер
    def write_logs(self):
        for core in self.cores:
            core.write_log()