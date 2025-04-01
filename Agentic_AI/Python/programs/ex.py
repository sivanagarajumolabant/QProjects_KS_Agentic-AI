# list = [2, 4, 5, 6, 9]

x = lambda a, b: a * b
print(type(x))
print(x(5,6))

your_string = "aaabbbccaabb"

current = ''
mod_list = []
count = 0
for index, loop in enumerate(your_string):
    current = loop
    count = count + 1
    if index == len(your_string) - 1:
        current = str(count) + current
        mod_list.append(current)
        count = 0
    else:
        if your_string[index + 1] == current:
            continue
        else:
            print(current)
            current = str(count) + current
            print(current)
            mod_list.append(current)
            count = 0

print(mod_list)


inp = [('d', 3), ('a', 2), ('c', 1), ('b', 4)]


# Output: [(‘c’, 1), (‘a’, 2), (‘d’, 3), (‘b’, 4)]
#
# def sort_tuples():
#     a = inp
#     for i in range(0, len(a)):
#         for j in range(i + 1, len(a)):
#             if a[i][1] > a[j][1]:
#                 a[i], a[j] = a[j], a[i]
#
#     return a
#
# print(sort_tuples())

for i in range(len(inp)):
    for j in range(i+1, len(inp)):
        if inp[i][1]> inp[j][1]:
            inp[i],inp[j] = inp[j],inp[i]
            
            

print(inp)
