# str = 'nitin'

# def palindrome(str):
#     return str == str[::-1]

# data = palindrome(str)
# print(data)

# num = '123454321'
# def palindrome_int(num):
#     n = len(num)
#     first =  0
#     last = n-1
#     while (first < last):
#         if num[first] == num[last]:
#             first += 1
#             last -=1
#         else:
#             return False
#     return True

# data1 =palindrome_int(num)
# print(data1)



# def fib(n):
#     a, b = 0 ,1
#     nums_list =[]
#     for i in range(n):
#         a, b= b, a+b
#         nums_list.append(a)
#     return nums_list
        
    
    
# fib_data = fib(20)
# print(fib_data)


str_data1 = 'aaabbbbbbcccdddffffffff'

dict_data = {}
forming_str = ''
for i in str_data1:
    if i in dict_data:
        dict_data[i] += 1
    else:
        dict_data[i] =1
        print(i)
        forming_str = forming_str+i+str(dict_data[i])
print(dict_data)