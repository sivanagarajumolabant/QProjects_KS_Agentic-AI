list_data = [1,2, 5,7]

import copy
list2 = copy.copy(list_data)
list2[0] = 20
print(list_data)
print(list2)

list_data = [[1,2], [5,7]]

import copy
list2 = copy.copy(list_data)
list2[0][0] = 20
print(list_data)
print(list2)


list_data = [1,2, 5,7]

import copy
list2 = copy.deepcopy(list_data)
list2[0] = 20
print(list_data)
print(list2)


list_data = [[1,2], [5,7]]

import copy
list2 = copy.deepcopy(list_data)
list2[0][0] = 20
print(list_data)
print(list2)