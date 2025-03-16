from pickle import load
import numpy as np


model_data = load(open('diabetic.pkl', 'rb'))
scaler = load(open('scalerdata.pkl', 'rb'))


# 0----> non diabetic
# 1----> Diabetic
# making input data predictive system
input_data = [5, 109, 75, 26, 0, 36, 0.546, 60]
array_input_data = np.asarray(input_data)
reshaped_data = array_input_data.reshape(1, -1)
standard_data = scaler.transform(reshaped_data)

pred = model_data.predict(standard_data)
print(pred)