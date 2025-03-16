import reg
import numpy as np
from pickle import load


def testing():
    # input data prediction

    li_model = load(open('cpmodel_li.pkl', 'rb'))

    # input data prediction
    # input_data = [2013,9.54,43000,1,0,0,0]#4.75
    input_data = [2014, 6.87, 42450, 1, 0, 0, 0]  # 4.6

    array_data = np.asarray(input_data)
    reshaped_data = array_data.reshape(1, -1)
    pred = li_model.predict(reshaped_data)
    print(pred)


testing()
