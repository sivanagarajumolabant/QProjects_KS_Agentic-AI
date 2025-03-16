# class Animal(object):
#     def __init__(self, name, age):
#         self.name = name
#         self.age = age
#
#     def __str__(self):
#         return "%s, %s" % (self.age, self.name)
#
#     def __repr__(self):
#         return "%s, %s" % (self.age, self.name)
#
#
# t = Animal("cat", 4)
# print(t)


class Sample:
    a = 500
    b = 99

    def outer_fun(self):
        print('Outer Function Enter...')
        print(self.b)
        b = self.b+1
        print(b)
        print(self.a)
        self.a = 501
        print(self.a)
        print('Outer Function')

        def inner_function():
            nonlocal b
            b = b + 1
            print('inner Function')
            return b

        return inner_function()

    @classmethod
    def class_method(cls):
        print('Class Method')
        print("Class var ", cls.a)
        cls.a = 503
        return cls.a

    @staticmethod
    def static_method():
        print('Static Method')
        print(Sample.a)
        return Sample.a

obj = Sample()
print(obj.outer_fun())
print(Sample.class_method())
print(obj.class_method())
print(obj.static_method())
