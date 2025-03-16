import reg
import numpy as np
from pickle import load


def testing():

    model = load(open('himodel.pkl', 'rb'))

    input_data = (31, 1, 25.74, 0, 1, 0)

    # changing input_data to a numpy array
    input_data_as_numpy_array = np.asarray(input_data)

    # reshape the array
    input_data_reshaped = input_data_as_numpy_array.reshape(1, -1)

    prediction = model.predict(input_data_reshaped)
    print(prediction)

    print('The insurance cost is USD ', prediction[0])


testing()
