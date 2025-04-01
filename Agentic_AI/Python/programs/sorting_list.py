listdata = [1, 4, 82, 3, -1, 0]

# Bubble Sort implementation
n = len(listdata)
for i in range(n):
    for j in range(0, n - i - 1):
        if listdata[j] > listdata[j + 1]:
            # Swap the elements
            listdata[j], listdata[j + 1] = listdata[j + 1], listdata[j]

print(listdata)  # Output: [-1, 0, 1, 3, 4, 82]


for i in range(0, len(listdata)):
    for j in range(i+1, len(listdata)):
        if listdata[i] > listdata[j]:
            listdata[i], listdata[j] = listdata[j], listdata[i]
            
print(listdata)