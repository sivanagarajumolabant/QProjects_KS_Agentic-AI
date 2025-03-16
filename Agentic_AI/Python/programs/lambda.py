def data():
    return [lambda x: i * x for i in range(5)]

# def data():
#     return [lambda x, i=i: i * x for i in range(5)]
call_test = data()

print(call_test)
for i in call_test:
    print(i)
    print(i(20))


def call_add(a):
    return a*a

result =  list(map(call_add, [1,2,3,4,5]))
print(result)


from functools import reduce
lst = [1,2,3,4,5]

mod_list = list(map(lambda x:x*2, lst))
print(mod_list)

mod_list = list(filter(lambda x:x%2==0, lst))
print(mod_list)


mod_list = reduce(lambda x,y:x+y, lst)
print(mod_list)