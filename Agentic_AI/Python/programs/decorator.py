
def addition(func):
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        return result
    return wrapper

@addition
def simple_fun(a, b):
    return a + b

print(simple_fun(4,5))



def log_decorator(func):
    def wrapper_fun(*args, **kwargs):
        modified_args = list(args)
        if modified_args:
            modified_args[0] = -(modified_args[0])
        result = func(*modified_args, **kwargs)
        return result
    return wrapper_fun

@log_decorator
def add(a,b):
    return a+b

result = add(4,5)
print(result)