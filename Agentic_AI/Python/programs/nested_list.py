def nested_fun(lst):
    list_mod = []
    for i in lst:
        if isinstance(i, list):
            list_mod.extend(nested_fun(i))
        else:
            list_mod.append(i)
    return list_mod


nested_li = [1, [2, [3, 4], 5], 6, [7, [8, 9]]]
print(nested_fun(nested_li))


def nested_fun(lst):
    list_mod = []
    for i in lst:
        if isinstance(i, tuple):
            list_mod.extend(nested_fun(i))
        else:
            list_mod.append(i)
    return list_mod


nested_li = [1, (2, (3, 4), 5), 6, (7, (8, 9))]
print(nested_fun(nested_li))



def flatten_list(nested_li):
    for item in nested_li:
        if isinstance(item, list):
            yield from flatten_list(item)
        else:
            yield item

nested_li = [1, [2, [3, 4], 5], 6, [7, [8, 9]]]
flat_list = list(flatten_list(nested_li))
print(flat_list)
