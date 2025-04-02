import time


class SingletonMeta(type):
    _instance = {}
    
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instance:
            cls._instance[cls] = super().__call__(*args,**kwargs)
        return cls._instance[cls]
     
def time_decorator(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        print(f"execution time :", {end_time - start_time})
        print("result", result)
        return result
    return wrapper
        
        
class Stringdecoding(metaclass= SingletonMeta):
    # str = ab2[c]3[xy]
    # output = abccxyxyxy
    
    @time_decorator
    def decode(self, s:str) -> str:
        stack = []
        num = 0
        curent_string = ""
        
        for char in s:
            if char.isdigit():
                num = num * 10 + int(char)
            elif char =='[':
                stack.append((curent_string, num))
                curent_string = ""
                num = 0
            elif char == ']':
                prev_string, repeat_times = stack.pop()
                curent_string = prev_string+curent_string*repeat_times
            else:
                curent_string += char
        return curent_string
                
# success test case             
def test_decoder(input_str,expected_output ):
    decoder = Stringdecoding()
    assert decoder.decode(input_str) == expected_output
    print("Test Passed")
        
if __name__=="__main__":
    input_str1 = "ab2[c]3[xy]"
    expected_output1 = "abccxyxyxy"
    test_decoder(input_str1, expected_output1)
    print("=====================================")
    input_str2 = "ab2[c]3[xy]"
    expected_output2 = "abccxyxyxyyy"
    test_decoder(input_str2, expected_output2)
    

                
                
                
                
                
                
                
                
                
                