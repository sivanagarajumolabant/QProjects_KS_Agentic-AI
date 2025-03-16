from sklearn.preprocessing import StandardScaler
import numpy as np
from pickle import load


def testing():
    # load Diabetic pickle data
    model_data = load(open('perkmodel.pkl', 'rb'))
    # making input data predictive system
    input_data = [119.992, 157.302, 74.997, 0.00784, 0.00007, 0.0037, 0.00554, 0.01109, 0.04374, 0.426, 0.02182, 0.0313,
                  0.02971, 0.06545, 0.02211, 21.033, 0.414783, 0.815285, -4.813031, 0.266482, 2.301442, 0.284654]  # 1
    array_input_data = np.asarray(input_data)
    reshaped_data = array_input_data.reshape(1, -1)

    # standadize the data before spliiting train and test data
    scaler = load(open('perkscaler.pkl', 'rb'))
    # scaler.fit(reshaped_data)
    standard_data = scaler.transform(reshaped_data)

    pred = model_data.predict(standard_data)
    print(pred)


testing()
