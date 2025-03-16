from pickle import load
import numpy as np


def testing():
    model = load(open('sonar_rock_model.pkl', 'rb'))
    # input data prediction system
    input_data = [0.0158, 0.0239, 0.0150, 0.0494, 0.0988, 0.1425, 0.1463, 0.1219, 0.1697, 0.1923, 0.2361, 0.2719,
                  0.3049, 0.2986, 0.2226, 0.1745, 0.2459, 0.3100, 0.3572, 0.4283, 0.4268, 0.3735, 0.4585, 0.6094,
                  0.7221, 0.7595, 0.8706, 1.0000, 0.9815, 0.7187, 0.5848, 0.4192, 0.3756, 0.3263, 0.1944, 0.1394,
                  0.1670, 0.1275, 0.1666, 0.2574, 0.2258, 0.2777, 0.1613, 0.1335, 0.1976, 0.1234, 0.1554, 0.1057,
                  0.0490, 0.0097, 0.0223, 0.0121, 0.0108, 0.0057, 0.0028, 0.0079, 0.0034, 0.0046, 0.0022, 0.0021]
    array_input_data = np.asarray(input_data)
    # reshape data
    reshaped_data = array_input_data.reshape(1, -1)

    pred_val = model.predict(reshaped_data)
    print(pred_val)



testing()
