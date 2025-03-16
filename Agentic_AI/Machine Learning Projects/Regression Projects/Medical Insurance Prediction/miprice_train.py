import pandas as pd
import sklearn.datasets
import numpy as np
from sklearn import metrics
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from pickle import dump


def training():
    dataset = pd.read_csv('insurance.csv')

    # encoding sex column
    dataset.replace({'sex': {'male': 0, 'female': 1}}, inplace=True)

    # encoding 'smoker' column
    dataset.replace({'smoker': {'yes': 0, 'no': 1}}, inplace=True)

    # encoding 'region' column
    dataset.replace({'region': {'southeast': 0, 'southwest': 1, 'northeast': 2, 'northwest': 3}},
                    inplace=True)

    # dividing features
    X = dataset.drop(columns='charges', axis=1)
    Y = dataset['charges']

    # divinding train and test split
    # split data into two parts
    X_train, X_test, Y_train, Y_test = train_test_split(X, Y, test_size=0.2, random_state=2)

    # apply model
    model = LinearRegression()
    model.fit(X_train, Y_train)
    dump(model, open('himodel.pkl', 'wb'))

    # predict on training data and accuracy score (R2 score)
    x_train_pred = model.predict(X_train)
    acc_x_train_r2 = metrics.r2_score(Y_train, x_train_pred)
    # acc_x_train_mae = metrics.mean_absolute_error(Y_train, x_train_pred)
    print("r2 score ", acc_x_train_r2)
    # print("mean absolute error ", acc_x_train_mae)

    # predict on testing data and accuracy score
    x_test_pred = model.predict(X_test)
    acc_x_test_re = metrics.r2_score(Y_test, x_test_pred)
    # acc_x_test_mae = metrics.mean_absolute_error(Y_test, x_test_pred)
    print("r2 score ", acc_x_test_re)
    # print("mean absolute error ", acc_x_test_mae)

    input_data = (31, 1, 25.74, 0, 1, 0)

    # changing input_data to a numpy array
    input_data_as_numpy_array = np.asarray(input_data)

    # reshape the array
    input_data_reshaped = input_data_as_numpy_array.reshape(1, -1)

    prediction = model.predict(input_data_reshaped)
    print(prediction)

    print('The insurance cost is USD ', prediction[0])


training()
