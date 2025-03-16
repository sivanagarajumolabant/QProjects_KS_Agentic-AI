import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from sklearn import svm
from sklearn.preprocessing import StandardScaler
from pickle import dump


def training():
    dataset = pd.read_csv('diabetes.csv')
    # print(dataset)
    # print(dataset.isnull().sum())
    # print(dataset.describe())
    # print(dataset.groupby('Outcome').mean())

    # Divide the target and features
    X = dataset.drop(columns='Outcome', axis=1)
    Y = dataset['Outcome']
    # print(X,Y)

    # standadize the data before spliiting train and test data
    scaler = StandardScaler()
    scaler.fit(X)
    dump(scaler,open('scalerdata.pkl','wb'))
    standard_data = scaler.transform(X)

    X = standard_data
    Y = dataset['Outcome']
    # print(X,Y)

    # spliiting the data
    X_train, X_test, Y_train, Y_test = train_test_split(X, Y, stratify=Y, random_state=2, test_size=0.2)
    # print(X.shape)
    # print(X_train.shape)
    # print(X_test.shape)

    # apply svm model and training
    model = svm.SVC(kernel='linear')
    model.fit(X_train, Y_train)
    # making pickle module for production
    dump(model,open('diabetic.pkl','wb'))

    # training data accuracy
    x_train_pred = model.predict(X_train)
    train_acc_data = accuracy_score(x_train_pred, Y_train)
    print("training acuracy", train_acc_data)

    # test data accuracy
    x_test_pred = model.predict(X_test)
    test_acc_data = accuracy_score(x_test_pred, Y_test)
    print("training acuracy", test_acc_data)

    # # 0----> non diabetic
    # # 1----> Diabetic
    # # making input data predictive system
    # input_data = [3,88,58,11,54,24.8,0.267,22]
    # array_input_data = np.asarray(input_data)
    # reshaped_data = array_input_data.reshape(1,-1)
    #
    # # standadize the data before spliiting train and test data
    # scaler = StandardScaler()
    # scaler.fit(reshaped_data)
    # standard_data = scaler.transform(reshaped_data)
    #
    # pred = model.predict(standard_data)
    # print(pred)

training()
