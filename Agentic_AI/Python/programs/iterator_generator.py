def create_gen(max):
    current = 0
    while current < max:
        current += 1
        yield current


for i in create_gen(3):
    print(i)


class iteratorclass():
    def __init__(self, max):
        self.max = max
        self.current = 0

    def __iter__(self):
        return self

    def __next__(self):
        if self.current < self.max:
            self.current = self.current + 1
            return self.current
        else:
            raise StopIteration


obj = iteratorclass(3)
for i in obj:
    print(i)

list_data = [1, 2, 3, 4, 5, 6]
print('================')
iterdata = iter(list_data)
print(next(iterdata))
print(next(iterdata))
print(next(iterdata))

def list_example(lst):
    for i in lst:
        yield i

gene = list_example([1,2,3,4,5])
print(next(gene))
