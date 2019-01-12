class PriorityQueue():
    def __init__(self):
        self.queue = []

    def __str__(self):
        return self.queue.__str__()

    def __iter__(self):
        for priority in self.queue:
            yield priority[0]

    def enqueue(self, element, priority):
        temp = self.queue.copy()
        if len(temp) == 0:
            self.queue.insert(0, (element, priority))
        for idx, elem in enumerate(temp):
            if elem[1] < priority:
                self.queue.insert(idx, (element, priority))
                break
            if idx == len(self.queue) - 1:
                self.queue.insert(idx+1, (element, priority))

    def dequeue(self):
        return self.queue.pop(0)

    def delete(self, element):
        index = None
        for idx, e in enumerate(self.queue):
            if e[0] == element:
                index = idx
                break
        if index != None:
            del self.queue[index]

    def reprioritize(self, element, priority):
        self.delete(element)
        if priority > 0:
            self.enqueue(element, priority)

    def isEmpty(self):
        return len(self.queue) == 0
