class Singleton:
    instance = None
    
    def __new__(cls):
        if cls.instance is None:
            cls.instance = super(Singleton, cls).__new__(cls)
        return cls.instance
            
obj1 = Singleton()
obj2 = Singleton()
print(obj1 is obj2)

import threading

def Singleton():
    instance = None
    lock = threading.Lock()
    def __new__(cls):
        if cls.instance is None:
            with cls.lock:
                if cls.instance is None:
                    cls.instance =  super(Singleton, cls).__new__(cls)
        return cls.instance

obj1 = Singleton()
obj2 = Singleton()
print(obj1 is obj2)
            

            
            
            
            