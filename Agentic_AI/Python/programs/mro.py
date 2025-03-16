class A:
    def hello(self):
        print("Hello from A")

class B(A):
    def hello(self):
        print("Hello from B")

class C(A):
    def hello(self):
        print("Hello from C")

class D(B, C):
    pass

d = D()
print(D.mro())
d.hello()  # Output: Hello from B (due to MRO order)
