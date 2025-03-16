from pickle import load
import numpy as np


def testing():
    model = load(open('titanicmodel.pkl', 'rb'))
    # making input data
    input_data = [3, 0, 2, 3, 1, 0]  # 0
    array_input_data = np.asarray(input_data)
    reshaped_data = array_input_data.reshape(1, -1)
    pred = model.predict(reshaped_data)
    print(pred)



testing()
