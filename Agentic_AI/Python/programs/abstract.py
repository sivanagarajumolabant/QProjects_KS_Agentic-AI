from abc import ABC, abstractmethod

class Animal(ABC):
    @abstractmethod
    def speak(self):
        pass

class Dog(Animal):
    def speak(self):
        print("Dog barks")

class Cat(Animal):
    def speak(self):
        print("Cat meows")

# Cannot instantiate abstract class Animal directly
# animal = Animal()  # TypeError: Can't instantiate abstract class Animal with abstract method speak

dog = Dog()
dog.speak()  # Dog barks

cat = Cat()
cat.speak()  # Cat meows
