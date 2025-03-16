str = "learning python"

print(str[::-1])
print(''.join(reversed(str)))

str_rev  = ''
leng  = len(str)-1

while leng>=0:
    str_rev = str_rev+str[leng]
    leng = leng-1

print(str_rev)


str1 = "a4b6c7"
for i in str1:
    if i.strip().isalpha():
        pass


