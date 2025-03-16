import numpy as np

arr = np.array([1, 2, 3, 4])
result = np.where(arr > 2, arr * 2, arr)  # If element > 2, multiply by 2, else leave unchanged
print(result)  # Output: [1 4 6 4]



zeros_array = np.zeros((3, 3))  # 3x3 array of zeros
ones_array = np.ones((2, 2))  # 2x2 array of ones
random_array = np.random.rand(2, 3)  # 2x3 array of random values between 0 and 1

print(zeros_array)
print(ones_array)
print(random_array)



a = np.array([1, 2, 3])
b = np.array([4, 5, 6])

print(a + b)  # Element-wise addition
print(a * b)  # Element-wise multiplication
print(a ** 2)  # Square each element


arr = np.array([1, 2, 3, 4, 5, 6])
reshaped_arr = arr.reshape(2, 3)  # Convert 1D array to 2x3 matrix

print(reshaped_arr)


print('==================')

arr1 = np.arange(1, 10, 2)  # [1, 3, 5, 7, 9]
print(arr1)
arr2 = np.linspace(0, 1, 5)  # 5 evenly spaced values between 0 and 1
print(arr2)

arr = np.array([[1, 2], [3, 4]])
r = arr.ravel()
print(r)
f = arr.flatten()
print(f)
