from pickle import load
import numpy as np


def testing():
    model = load(open('loanmodel.pkl', 'rb'))
    # input data prediction system
    # input_data = [0,0,0,0,1,9560,0,191,360,1,0] #Y
    # input_data = [0,0,0,0,0,2799,2253,122,360,1,0] #Y
    input_data = [0,0,0,1,0,2600,1911,116,360,0,0] #N

    array_input_data = np.asarray(input_data)
    # reshape data
    reshaped_data = array_input_data.reshape(1, -1)

    pred_val = model.predict(reshaped_data)
    print(pred_val)


testing()
