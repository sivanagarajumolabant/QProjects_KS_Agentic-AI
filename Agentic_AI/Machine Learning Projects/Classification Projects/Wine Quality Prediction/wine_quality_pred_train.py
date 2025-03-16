import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from sklearn.ensemble import RandomForestClassifier
from pickle import dump


def training():
    dataset = pd.read_csv('winequality-red.csv')
    # print(dataset.head())
    # print(dataset.shape)
    # print(dataset.isnull().sum())
    # print(dataset.describe())
    dataset['quality'] = dataset['quality'].apply(lambda x: 1 if x >= 7 else 0)
    # print(dataset)
    X = dataset.drop(columns='quality', axis=1)
    Y = dataset['quality']
    # spliiting the data
    X_train, X_test, Y_train, Y_test = train_test_split(X, Y, random_state=3, test_size=0.2)

    # apply svm model and training
    model = RandomForestClassifier()
    model.fit(X_train, Y_train)
    # making pickle module for production
    dump(model, open('winequality.pkl', 'wb'))

    # training data accuracy
    x_train_pred = model.predict(X_train)
    train_acc_data = accuracy_score(x_train_pred, Y_train)
    print("training acuracy", train_acc_data)

    # test data accuracy
    x_test_pred = model.predict(X_test)
    test_acc_data = accuracy_score(x_test_pred, Y_test)
    print("training acuracy", test_acc_data)

    # make predictive system
    # input_data =[6.0,0.31,0.47,3.6,0.067,18.0,42.0,0.99549,3.39,0.66,11.0] #6
    input_data =[7.4,0.25,0.29,2.2,0.054000000000000006,19.0,49.0,0.99666,3.4,0.76,10.9] #7
    array_input_data = np.asarray(input_data)
    reshaped_data = array_input_data.reshape(1,-1)
    pred = model.predict(reshaped_data)
    print(pred)


training()
