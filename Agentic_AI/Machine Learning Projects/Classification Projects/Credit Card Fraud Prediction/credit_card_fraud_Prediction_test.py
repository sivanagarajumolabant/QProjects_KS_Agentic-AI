from pickle import load
import numpy as np


def testing():
    model = load(open('credit.pkl', 'rb'))
    # input data prediction system
    input_data = [1, -0.966271712, -0.185226008, 1.79299334, -0.863291275, -0.01030888, 1.247203168, 0.23760894,
                  0.377435875, -1.387024063, -0.054951922, -0.226487264, 0.178228226, 0.50775687, -0.287923745,
                  -0.631418118, -1.059647245, -0.684092786, 1.965775003, -1.23262197, -0.208037781, -0.108300452,
                  0.005273597, -0.190320519, -1.175575332, 0.647376035, -0.221928844, 0.062722849, 0.061457629,
                  123.5]  # 0

    # input_data = [43, 1, 0, 120, 177, 0, 0, 120, 1, 2.5, 1, 0, 3]  # 0
    array_input_data = np.asarray(input_data)
    # reshape data
    reshaped_data = array_input_data.reshape(1, -1)

    pred_val = model.predict(reshaped_data)
    print(pred_val)


testing()
