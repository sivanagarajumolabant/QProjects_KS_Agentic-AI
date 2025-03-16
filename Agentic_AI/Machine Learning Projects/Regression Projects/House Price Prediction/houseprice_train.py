import pandas as pd
import sklearn.datasets
import numpy as np
from sklearn import metrics
from sklearn.model_selection import train_test_split
from xgboost import XGBRegressor
from pickle import dump


def training():
    # read csv file using pandas
    hp_dataset = sklearn.datasets.load_boston()
    feature_data = pd.DataFrame(hp_dataset.data, columns=hp_dataset.feature_names)
    # print(feature_data.columns)

    target_data = pd.DataFrame(hp_dataset.target)
    target_data.rename(columns={0: 'Label'}, inplace=True)

    dataset = pd.concat([feature_data, target_data], axis=1)
    # print(dataset[:].values)
    # print(dataset.loc[1,:])

    # dividing features
    X = dataset.drop(columns='Label')
    Y = dataset['Label']

    # print(X[:1])
    # print(Y[:1])
    # divinding train and test split
    # split data into two parts
    X_train, X_test, Y_train, Y_test = train_test_split(X, Y, test_size=0.2, random_state=2)

    # apply model
    model = XGBRegressor()
    model.fit(X_train, Y_train)
    dump(model, open('hpmodel.pkl', 'wb'))

    # predict on training data and accuracy score (R2 score)
    x_train_pred = model.predict(X_train)
    acc_x_train_r2 = metrics.r2_score(Y_train, x_train_pred)
    acc_x_train_mae = metrics.mean_absolute_error(Y_train, x_train_pred)
    print("r2 score ", acc_x_train_r2)
    print("mean absolute error ", acc_x_train_mae)

    # predict on testing data and accuracy score
    x_test_pred = model.predict(X_test)
    acc_x_test_re = metrics.r2_score(Y_test, x_test_pred)
    acc_x_test_mae = metrics.mean_absolute_error(Y_test, x_test_pred)
    print("r2 score ", acc_x_test_re)
    print("mean absolute error ", acc_x_test_mae)

    # # input data prediction
    # input_data = [0.00632,18.0,2.31,0.0,0.538,6.575,65.2,4.09,1.0,296.0,15.3,396.9,4.98]
    #
    # array_data = np.asarray(input_data)
    # reshaped_data = array_data.reshape(1, -1)
    # pred = model.predict(reshaped_data)
    # print(pred)


training()
