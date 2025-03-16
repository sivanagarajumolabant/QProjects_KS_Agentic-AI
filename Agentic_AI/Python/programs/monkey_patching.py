class MyClass:
    def greet(self):
        return "Hello, World!"

obj = MyClass()
print(obj.greet()) 


def new_greet(self):
    return "Hello, Monkey Patching!"

MyClass.greet = new_greet

print(obj.greet())
