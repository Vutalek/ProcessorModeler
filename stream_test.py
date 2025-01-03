from lib.PCIe import PCIe

class Printer:
    def __init__(self):
        self.tasks = []

    def receive(self, frame):
        if frame.islast == 1:
            self.__reconstruct(frame)

    def __reconstruct(self, last_frame):
        if last_frame.task_id == -1:
            return
        else:
            self.tasks.append(last_frame.task)

    def print_tasks(self):
        print("Total tasks: ", len(self.tasks))
        space = 0
        for task in self.tasks:
            space += task.data
        print("Total space: ", space)

printer = Printer()
pcie = PCIe("test")
pcie.config()
for i in range(len(pcie.lanes)):
    pcie.connect_receiver(lane = i, receiver = printer)
pcie.create_channel([0, 1, 2, 3])
out = [0]
tx = pcie.start_transmission(out, 0)
tx.join()

printer.print_tasks()
print(f"Transmission time: {out[0]}")