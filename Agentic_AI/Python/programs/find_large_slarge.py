list_data = [1, 300,700, 298,701, 400,800,890, 302, 600, 650, 56, 30, 12, 500, 1000]

slarge = float('-inf')
large = float('-inf')


for i in range(len(list_data)):
    if list_data[i] > large:
        slarge = large
        large = list_data[i]
    elif large != slarge and slarge > list_data[i]:
        slarge = list_data[i]
        
print(large)
print(slarge)     

print('=========================================================================')

list_data = [1, 300,700,3, 298,701, 400,800, 302, 600, 650, 56, 30, 12, 500, 1000]

small = float('inf')
ssmall = float('inf')


for i in range(len(list_data)):
    if list_data[i] < small:
        ssmall = small
        small = list_data[i]
    elif list_data[i] < ssmall and list_data[i] != small:
        ssmall = list_data[i]
    
print(small)
print(ssmall)     