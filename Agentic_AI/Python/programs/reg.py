import re

# search string with specific words startswith and endswith

str = 'The Qmigrator Tool'

x = re.search(r'The.*Tool$', str)

# findall(), search(), sub(), split()
# print(x)

# [0-9]

me_0 = re.findall('[a-q]', str)
print(me_0,'=========')


# txt = "That will be 59 dollars"
#
# #Find all digit characters:
#
# d = re.findall("\d", txt)
# print(d)

# txt = "hello planet"
#
# #Search for a sequence that starts with "he", followed by two (any) characters, and an "o":
#
# x = re.findall("he....p", txt)
# print(x)

#
# x = re.findall("^hello.*et$", txt)
# if x:
#   print("Yes, the string starts with 'hello' and ends with et")
# else:
#   print("No match")


txt = "hello planet"

#Search for a sequence that starts with "he", followed by 0 or more  (any) characters, and an "o":

x = re.findall("he.*et", txt)
y = re.findall("hello...an", txt)
# print(x)
print(y,'============================')
z = re.findall("hello.+et", txt)
print(z)
a = re.findall("hello.{2}lanet", txt)
# print(a)
b = re.findall("hello(.{2})lanet", txt)
# print(b)
# c = re.findall("hello|lanet", txt)
# print(c)
d = re.findall("\AHello", txt, re.IGNORECASE)
print(d)
e = re.findall("\Ahello", txt )
# print(e)
f = re.findall("\Bnet", txt )
print(f)
# g = re.findall(r"\d[0-9]")

#
# print(x)
# print(y)
# print(z)
# print(a)
# print(b)
# print(c)
# print(e)
# print(f)

txt1 = "The rain in dra Spain i"
xt = re.search(r"\bi\w+", txt1)
print(xt,'========')
