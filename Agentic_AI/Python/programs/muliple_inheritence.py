class A:
    def exea(self):
        print("Execute A exea")
        return "A class execution"

class B(A):
    def exea(self):
        print("Execute B exea")
        return "B class execution"
    
class C(B,A):
    # def exea(self):
    #     print("Execute C exec")
    #     return "C class execution"
    pass
    
print(C.mro())
obj = C()
print(obj.exea())