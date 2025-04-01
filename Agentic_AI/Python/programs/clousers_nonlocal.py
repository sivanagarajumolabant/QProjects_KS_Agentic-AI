def outer_function(outer_variable):
    def inner_function(inner_variable):
        # inner_function can access both outer_variable and inner_variable
        print(f"Outer variable: {outer_variable}")
        print(f"Inner variable: {inner_variable}")

    return inner_function


# Create a closure by calling outer_function
closure = outer_function("I am outer!")

# The closure has access to the variable from the outer function
closure("I am inner!")


def counter():
    count = 0  # This variable is enclosed in the closure

    def increment():
        nonlocal count  # nonlocal tells Python to use the variable from the outer scope
        count += 1
        return count

    return increment


# Create a counter closure
my_counter = counter()

# Call the closure multiple times
print(my_counter())  # 1
print(my_counter())  # 2
print(my_counter())  # 3



def outer_function(x):
    # This is the outer function, which defines a variable `x`
    def inner_function(y):
        # The inner function accesses `x` from the outer function's scope
        return x + y
    return inner_function  # Returning the inner function as a closure

# Creating a closure by calling outer_function with a value for `x`
closure = outer_function(10)
print(closure)
print(type(closure))

# Now, even though outer_function has finished executing, 
# the inner_function still remembers the value of `x` (which is 10).
print(closure(5))  # Output: 15 (10 + 5)



def main_func():
    count = 0
    def count_func():
        nonlocal count
        count = count +1
        return count
    return count_func
    
outer_func = main_func()
print(outer_func())
print(outer_func())
print(outer_func())
