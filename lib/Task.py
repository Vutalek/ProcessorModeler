# type - тип задачи
# cost - количество тактов, необходимых для решения этой задачи
# data - объём пользовательских данных в байтах
class Task:
    def __init__(self, type: str, cost: int, data: int):
        self.type = type
        self.cost = cost
        self.data = data