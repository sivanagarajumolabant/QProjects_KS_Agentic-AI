def decorator_fun_sub(func):
    def inner(*args, **kwargs):
        values = func(*args, **kwargs)
        return values

    return inner

@decorator_fun_sub
def subtract_number(a, b):
    print("subtract ", a-b)
    return a-b

subtract_number(4,3)

def decorator_fun(func):
    def sample(*args, **kwargs):
        print('before execution', *args, **kwargs)
        return_values = func(*args, **kwargs)
        print('After execution', return_values, *args, **kwargs)
        return return_values

    return sample

@decorator_fun
def sum_numbers(a, b):
    print('execution sum numbers')
    return a * b

print(sum_numbers(4,3))