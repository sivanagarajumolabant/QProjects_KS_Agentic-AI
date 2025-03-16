def fibnacci(n):
    fib_list = []
    a, b = 0, 1
    for i in range(n):
        fib_list.append(a)
        a, b = b, a + b
    return fib_list


print(fibnacci(20))
