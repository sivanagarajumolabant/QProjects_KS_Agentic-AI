# class Employee():
#     def __init__(self, name, sal, count=0):
#         self.name = name
#         self.sal = sal
#
#     #
#     # def add_employee(self, name, sal):
#     #     print(name)
#
#     def display_count(self):
#         # print(count)
#         return
#
#
# e1 = Employee('siva', 1000)
# e2 = Employee('ravi', 1000)
# e3 = Employee('siva1', 1000)

list = [2, 52, 34, 5, 6]

largest = list[0]
second_lar = list[0]
for i in range(len(list)):
    if list[i] > largest:
        largest = list[i]

for j in range(len(list)):
    if list[j]>second_lar and list[j]!= largest:
        second_lar = list[j]
print(largest)
print(second_lar)


