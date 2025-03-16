import reg
import numpy as np
from pickle import load


def testing():
    # input data prediction

    model = load(open('gpmodel.pkl', 'rb'))


    # input data prediction
    input_data = [1447.160034, 78.370003, 15.285, 1.474491]  # 85.57

    array_data = np.asarray(input_data)
    reshaped_data = array_data.reshape(1, -1)
    pred = model.predict(reshaped_data)
    print(pred)


testing()
