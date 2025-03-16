list = [1, 0, -3, 5, 8, 9]

# how to sort without using in built methods
new_list = []
while list:
    min = list[0]
    for i in list:
        if i < min:
            min = i
    new_list.append(min)
    list.remove(min)
# print(new_list)

# extract ip adresses from the string

str1 = "12.54.34.655"
import re

ip_addresses = re.findall(r'[0-9]+(?:\.[0-9]+){3}', str1)
# print(ip_addresses)


# sorting multiple list of tuples

lt = [('a', 3), ('b', 1), ('c', 4), ('d', 2)]

for i in range(len(lt)):
    for j in range(i + 1, len(lt)):
        if lt[i][1] > lt[j][1]:
            lt[i], lt[j] = lt[j], lt[i]
print(lt)

# counting occurences characters

your_string = "aaabbbccaabbeeeee"

current = ''
mod_list = []
count = 0
for index, loop in enumerate(your_string):
    current = loop
    count = count + 1
    if index == len(your_string) - 1:
        current = str(count * len(current)) + current
        mod_list.append(current)
        count = 0
    else:
        if your_string[index + 1] == current:
            continue
        else:
            current = str(count * len(current)) + current
            mod_list.append(current)
            count = 0

print(mod_list)
print(''.join(mod_list))
