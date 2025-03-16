class Circle:
    def __init__(self, radius):
        self._radius = radius

    @property
    def get_radius(self):
        return self._radius

    @get_radius.setter
    def set_radius(self, value):
        if value < 0:
            print("Radius cannot be negative.")
        else:
            self._radius = value

circle = Circle(5)
print(circle.get_radius)  # Accessing the property

circle.set_radius = 20  # Setting the property value
print(circle.get_radius)
