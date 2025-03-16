class A:
    def exea(self):
        print("Execute A exea")


class B(A):
    def exea(self):
        print("Execute B exea")

    def exeb(self):
        print("Execute B exeb")

class C(B):
    def exec(self):
        print("Execute C exec")
        return 1

obj = C()
print(obj.exea())


# method overriding

def overriding(object):
    result  =object.exec()
    return result


print('==========')
print(overriding(obj))