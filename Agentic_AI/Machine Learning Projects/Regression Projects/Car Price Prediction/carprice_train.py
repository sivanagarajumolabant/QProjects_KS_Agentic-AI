import pandas as pd
import sklearn.datasets
import numpy as np
from sklearn import metrics
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression,Lasso
from pickle import dump


def training():
    # read csv file using pandas
    dataset = pd.read_csv('car data.csv')

    # encoding "Fuel_Type" Column
    dataset.replace({'Fuel_Type': {'Petrol': 0, 'Diesel': 1, 'CNG': 2}}, inplace=True)

    # encoding "Seller_Type" Column
    dataset.replace({'Seller_Type': {'Dealer': 0, 'Individual': 1}}, inplace=True)

    # encoding "Transmission" Column
    dataset.replace({'Transmission': {'Manual': 0, 'Automatic': 1}}, inplace=True)

    # dividing features
    X = dataset.drop(['Car_Name', 'Selling_Price'], axis=1)
    Y = dataset['Selling_Price']

    # print(X[:1])
    # print(Y[:1])
    # divinding train and test split
    # split data into two parts
    X_train, X_test, Y_train, Y_test = train_test_split(X, Y, test_size=0.1, random_state=2)

    # apply Linear Regression model
    li_model = LinearRegression()
    li_model.fit(X_train, Y_train)
    dump(li_model, open('cpmodel_li.pkl', 'wb'))

    # predict on training data and accuracy score (R2 score)
    x_train_pred = li_model.predict(X_train)
    acc_x_train_r2 = metrics.r2_score(Y_train, x_train_pred)
    # acc_x_train_mae = metrics.mean_absolute_error(Y_train, x_train_pred)
    print("r2 score tarining Linear Reg", acc_x_train_r2)
    # print("mean absolute error ", acc_x_train_mae)

    # predict on testing data and accuracy score
    x_test_pred = li_model.predict(X_test)
    acc_x_test_re = metrics.r2_score(Y_test, x_test_pred)
    # acc_x_test_mae = metrics.mean_absolute_error(Y_test, x_test_pred)
    print("r2 score Testing Linear Reg", acc_x_test_re)
    # print("mean absolute error ", acc_x_test_mae)

    # apply Lasso Regression model
    lasso_model = Lasso()
    lasso_model.fit(X_train, Y_train)
    dump(lasso_model, open('cpmodel_lasso.pkl', 'wb'))

    # predict on training data and accuracy score (R2 score)
    x_train_pred = lasso_model.predict(X_train)
    acc_x_train_r2 = metrics.r2_score(Y_train, x_train_pred)
    # acc_x_train_mae = metrics.mean_absolute_error(Y_train, x_train_pred)
    print("r2 score Lasso Training", acc_x_train_r2)
    # print("mean absolute error ", acc_x_train_mae)

    # predict on testing data and accuracy score
    x_test_pred = lasso_model.predict(X_test)
    acc_x_test_re = metrics.r2_score(Y_test, x_test_pred)
    # acc_x_test_mae = metrics.mean_absolute_error(Y_test, x_test_pred)
    print("r2 score Lasso Testing", acc_x_test_re)
    # print("mean absolute error ", acc_x_test_mae)

    # input data prediction
    # input_data = [2013,9.54,43000,1,0,0,0]#4.75
    input_data = [2014,6.87,42450,1,0,0,0]#4.6

    array_data = np.asarray(input_data)
    reshaped_data = array_data.reshape(1, -1)
    pred = li_model.predict(reshaped_data)
    print(pred)


training()
