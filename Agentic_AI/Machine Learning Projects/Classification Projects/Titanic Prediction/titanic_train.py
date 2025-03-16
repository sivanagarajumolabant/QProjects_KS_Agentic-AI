import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from sklearn.linear_model import LogisticRegression
from pickle import dump


def training_data():
    dataset = pd.read_csv('titanic_train.csv')

    # pre processing steps
    dataset = dataset.drop(columns=['Cabin'], axis=1)
    # print(dataset.head())
    # print(dataset.isnull().sum())

    # replacing age with mean value
    dataset['Age'].fillna(dataset['Age'].mean(), inplace=True)
    # replacing embarked null values handling with mode
    dataset['Embarked'].fillna(dataset['Embarked'].mode()[0], inplace=True)

    dataset.replace({"Sex": {"male": 0, "female": 1}}, inplace=True)
    dataset.replace({"Embarked": {"S": 0, "C": 1, "Q": 2}}, inplace=True)

    dataset.drop(columns=['PassengerId', 'Name', 'Ticket', 'Fare'], inplace=True)
    # print(dataset.head())

    X = dataset.drop(columns='Survived', axis=1)
    Y = dataset['Survived']

    X_train, X_test, Y_train, Y_test = train_test_split(X, Y, stratify=Y, random_state=2, test_size=0.2)
    # print(X.shape)
    # print(X_train.shape)
    # print(X_test.shape)

    model  = LogisticRegression()
    model.fit(X_train,Y_train)
    dump(model,open('titanicmodel.pkl','wb'))

    # training
    train_pred = model.predict(X_train)
    acc_data_train = accuracy_score(train_pred,Y_train)
    print("Training Accuracy ", acc_data_train)
    #testing
    test_pred = model.predict(X_test)
    acc_data_test = accuracy_score(test_pred, Y_test)
    print("test Accuracy ", acc_data_test)


    # making input data
    input_data = [3,0,2,3,1,0] #0
    array_input_data = np.asarray(input_data)
    reshaped_data = array_input_data.reshape(1, -1)
    pred = model.predict(reshaped_data)
    print(pred)

training_data()
