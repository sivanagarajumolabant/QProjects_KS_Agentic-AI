def get_even_numbers(numbers):
    return [num for num in numbers if num % 2 == 0]

if __name__ == "__main__":
    numbers = list(range(1, 21))
    print("Even numbers:", get_even_numbers(numbers))
