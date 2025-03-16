import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from sklearn import svm
from sklearn.preprocessing import StandardScaler
from pickle import dump


def training():
    dataset = pd.read_csv('parkinsons.csv')
    # print(dataset.head())
    # print(dataset.isnull().sum())
    # print(dataset.describe())
    # print(dataset.groupby('Outcome').mean())

    # # Divide the target and features
    X = dataset.drop(columns=['status', 'name'], axis=1)
    Y = dataset['status']
    # # print(X,Y)
    #
    # standadize the data before spliiting train and test data
    scaler = StandardScaler()
    scaler.fit(X)
    dump(scaler, open('perkscaler.pkl', 'wb'))
    standard_data = scaler.transform(X)
    #
    X = standard_data
    Y = dataset['status']
    # # print(X,Y)
    #
    # spliiting the data
    X_train, X_test, Y_train, Y_test = train_test_split(X, Y, stratify=Y, random_state=1, test_size=0.2)
    # print(X.shape)
    # print(X_train.shape)
    # print(X_test.shape)
    #
    # apply svm model and training
    model = svm.SVC(kernel='linear')
    model.fit(X_train, Y_train)
    # making pickle module for production
    dump(model, open('perkmodel.pkl', 'wb'))

    # training data accuracy
    x_train_pred = model.predict(X_train)
    train_acc_data = accuracy_score(x_train_pred, Y_train)
    print("training acuracy", train_acc_data)

    # test data accuracy
    x_test_pred = model.predict(X_test)
    test_acc_data = accuracy_score(x_test_pred, Y_test)
    print("test acuracy", test_acc_data)

    # making input data predictive system
    input_data = [119.992, 157.302, 74.997, 0.00784, 0.00007, 0.0037, 0.00554, 0.01109, 0.04374, 0.426, 0.02182, 0.0313,
                  0.02971, 0.06545, 0.02211, 21.033, 0.414783, 0.815285, -4.813031, 0.266482, 2.301442, 0.284654]  # 1
    array_input_data = np.asarray(input_data)
    reshaped_data = array_input_data.reshape(1, -1)

    # standadize the data before spliiting train and test data
    scaler = StandardScaler()
    scaler.fit(reshaped_data)
    standard_data = scaler.transform(reshaped_data)

    pred = model.predict(standard_data)
    print(pred)


training()
