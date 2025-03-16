class Single:
    def __init__(self):
        self.name = 'Siva'  # public
        self.__password = 'siva@123'  # private
        self._address = 'Chinthal'  # protected
    
    @property
    def get_public_var(self):
        return self.name
    
    def get_address(self):
        return self._address
    
    def get_password(self):
        return self.__password
    
    @get_public_var.setter
    def set_public_var(self, value):
        self.name = value

# Creating an object of the class
data = Single()

# Accessing public variable through the property
print(data.get_public_var)  # Output: Siva

# Setting the name through the setter
data.set_public_var = 'Naga'

# Accessing updated name
print(data.get_public_var)  # Output: Naga

# Accessing private variable through getter
print(data.get_password())  # Output: siva@123

# Accessing protected variable
print(data.get_address())  # Output: Chinthal
