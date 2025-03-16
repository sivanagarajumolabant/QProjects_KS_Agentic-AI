lsit = [2, 7, 11, 15, 5, 4]
target = 9

data = {}
for i in lsit:
    diff = abs(target - i)
    if diff in lsit and i not in data:
        data[diff] = i

print(data)
