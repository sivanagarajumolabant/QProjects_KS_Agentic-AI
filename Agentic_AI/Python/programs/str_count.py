str = 'sivanagaraju'

str_count ={}

for i in str:
    if i in str_count:
        continue
    else:
        str_count[i] = str.count(i)

print(str_count)