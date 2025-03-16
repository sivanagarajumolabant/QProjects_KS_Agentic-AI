import numpy as np
from pickle import load


def testing():
    # load Diabetic pickle data
    model_data = load(open('winequality.pkl', 'rb'))
    # make predictive system
    input_data =[6.0,0.31,0.47,3.6,0.067,18.0,42.0,0.99549,3.39,0.66,11.0] #6
    # input_data = [7.4, 0.25, 0.29, 2.2, 0.054000000000000006, 19.0, 49.0, 0.99666, 3.4, 0.76, 10.9]  # 7
    array_input_data = np.asarray(input_data)
    reshaped_data = array_input_data.reshape(1, -1)
    pred = model_data.predict(reshaped_data)
    print(pred)


testing()
