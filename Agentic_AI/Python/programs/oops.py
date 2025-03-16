# Encapsulation

class BankAccount:
    def __init__(self, balance=0):
        self.__balance = balance  # Private attribute

    def deposit(self, amount):
        if amount > 0:
            self.__balance += amount
            print(f"Deposited: {amount}")

    def get_balance(self):
        return self.__balance

account = BankAccount()
account.deposit(100)
print(account.get_balance())  # Outputs: 100
# print(account.___balance)  # Raises AttributeError
print(account._BankAccount__balance) # alternative approach



# Abstraction

from abc import ABC, abstractmethod

class Animal(ABC):
    @abstractmethod
    def sound(self):
        pass

class Dog(Animal):
    def sound(self):
        return "Bark"

class Cat(Animal):
    def sound(self):
        return "Meow"

dog = Dog()
cat = Cat()
print(dog.sound())  # Outputs: Bark
print(cat.sound())  # Outputs: Meow




# Inheritance

class Vehicle:
    def __init__(self, brand):
        self.brand = brand

    def honk(self):
        return "Honk!"

class Car(Vehicle):
    def __init__(self, brand, model):
        super().__init__(brand)  # Call the constructor of the parent class
        self.model = model

    def honk(self):
        return "Car honk!"

car = Car("Toyota", "Corolla")
print(car.brand)  # Outputs: Toyota
print(car.model)  # Outputs: Corolla
print(car.honk())  # Outputs: Car honk!



# Ploymorphiosm

class Bird:
    def speak(self):
        return "Chirp"

class Dog:
    def speak(self):
        return "Bark"

def animal_sound(animal):
    print(animal.speak())

bird = Bird()
dog = Dog()
animal_sound(bird)  # Outputs: Chirp
animal_sound(dog)   # Outputs: Bark



# method overriding

class Parent:
    def show(self):
        return "Parent's show method"

class Child(Parent):
    def show(self):
        return "Child's show method"

child = Child()
print(child.show())  # Outputs: Child's show method



# method overloading
# using default arguments
class Example:
    def display(self, message="Hello"):
        print(message)

obj = Example()
obj.display()          # Outputs: Hello
obj.display("Hi!")    # Outputs: Hi!

# using *args/**kwargs
class Example:
    def display(self, *args):
        for arg in args:
            print(arg)

obj = Example()
obj.display("Hello", "World")  # Outputs: Hello \n World




# class methods & static methods
class MyClass:
    class_variable = "Class variable"

    @classmethod
    def class_method(cls):
        return cls.class_variable

    @staticmethod
    def static_method():
        return MyClass.class_variable

print(MyClass.class_method())  # Outputs: Class variable
print(MyClass.static_method())  # Outputs: Static method called
