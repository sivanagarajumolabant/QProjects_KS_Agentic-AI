my_dict = {'a': 1, 'b': 2}

# Using get()
print(my_dict.get('c',3))  # Outputs: Not Found
print(my_dict)
# Using setdefault()
value = my_dict.setdefault('c', 3)
print(value)             # Outputs: 3
print(my_dict)          # Outputs: {'a': 1, 'b': 2, 'c': 3}



print('==========================')
my_dict = {'b': 2, 'a': 1, 'c': 3}

print(sorted(my_dict.items()), '===========1')
# Sort by keys
sorted_by_keys = dict(sorted(my_dict.items()))
print(sorted_by_keys,'============2')  # Outputs: {'a': 1, 'b': 2, 'c': 3}

# Sort by values
sorted_by_values = dict(sorted(my_dict.items(), key=lambda item: item[1]))
print(sorted_by_values,'==============3')  # Outputs: {'a': 1, 'b': 2, 'c': 3}
