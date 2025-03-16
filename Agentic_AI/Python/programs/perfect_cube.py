input = "125 216 54 81 48 343 81 27 8 1"
list = input.split()


def is_perfect_cube(number):  # -> bool:
    """
    Indicates (with True/False) if the provided number is a perfect cube.
    """
    number = abs(number)  # Prevents errors due to negative numbers
    return round(number ** (1 / 3)) ** 3 == number


count = 0
for i in list:
    cond = is_perfect_cube(int(i.strip()))
    if cond:
        count = count + 1
print(count)
