from pickle import load
import numpy as np


def testing():
    model = load(open('heart.pkl', 'rb'))
    # input data prediction system
    input_data = [37,1,2,130,250,0,1,187,0,3.5,0,0,2] #1
    # input_data = [43, 1, 0, 120, 177, 0, 0, 120, 1, 2.5, 1, 0, 3]  # 0
    array_input_data = np.asarray(input_data)
    # reshape data
    reshaped_data = array_input_data.reshape(1, -1)

    pred_val = model.predict(reshaped_data)
    print(pred_val)



testing()
