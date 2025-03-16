def divide_numbers(a: int, b: int) -> int:
    try:
        data =  a / b
    except Exception as error:
        print('Division error')
        data = None
    else:
        print('try success')
        data = None
    finally:
        print('always executes')
        data = None
    return data
print(divide_numbers(2,0))