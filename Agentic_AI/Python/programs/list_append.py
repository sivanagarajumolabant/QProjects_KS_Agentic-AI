def list_data(value, lst=[]):
    lst.append(value)
    return lst


print(list_data(1))  # [1]
print(list_data(2))  # [2]
print(list_data(3))  # [3]

def list_data(value, lst=None):
    if lst is None:
        lst = []
    lst.append(value)
    return lst


print(list_data(1))  # [1
print(list_data(2))  # [1,2]
print(list_data(3))  # [1,2,3]
