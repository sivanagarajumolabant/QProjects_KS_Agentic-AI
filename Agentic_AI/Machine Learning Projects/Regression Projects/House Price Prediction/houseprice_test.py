import reg
import numpy as np
from pickle import load


def testing():
    # input data prediction
    # input data prediction
    input_data = [0.00632, 18.0, 2.31, 0.0, 0.538, 6.575, 65.2, 4.09, 1.0, 296.0, 15.3, 396.9, 4.98]
    array_data = np.asarray(input_data)
    reshaped_data = array_data.reshape(1, -1)
    model = load(open('hpmodel.pkl', 'rb'))
    pred = model.predict(reshaped_data)
    print(pred)


testing()
