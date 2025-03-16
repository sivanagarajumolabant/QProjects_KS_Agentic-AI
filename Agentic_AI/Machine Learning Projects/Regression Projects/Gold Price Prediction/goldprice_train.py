import pandas as pd
import sklearn.datasets
import numpy as np
from sklearn import metrics
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from pickle import dump


def training():
    # read csv file using pandas
    dataset = pd.read_csv('gld_price_data.csv')

    # dividing featuresc
    X = dataset.drop(['Date', 'GLD'], axis=1)
    Y = dataset['GLD']

    # split data into two parts
    X_train, X_test, Y_train, Y_test = train_test_split(X, Y, test_size=0.2, random_state=2)

    # apply model
    model = RandomForestRegressor()
    model.fit(X_train, Y_train)
    dump(model, open('gpmodel.pkl', 'wb'))

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

    # input data prediction
    input_data = [1447.160034,78.370003,15.285,1.474491] #85.57

    array_data = np.asarray(input_data)
    reshaped_data = array_data.reshape(1, -1)
    pred = model.predict(reshaped_data)
    print(pred)


training()
