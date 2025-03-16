class Bird:
    def speak(self):
        print("Bird chirps")

class Dog:
    def speak(self):
        print("Dog barks")

# Polymorphism: Both objects have a speak() method
def animal_sound(animal):
    animal.speak()

bird = Bird()
dog = Dog()

animal_sound(bird)  # Bird chirps
animal_sound(dog)   # Dog barks
