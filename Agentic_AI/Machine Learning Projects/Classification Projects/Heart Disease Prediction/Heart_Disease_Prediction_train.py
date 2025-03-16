import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from sklearn.linear_model import LogisticRegression
from pickle import dump


def training_data():
    dataset = pd.read_csv('heart.csv')
    # head data
    # print(dataset.head())
    # dataset shape
    # print(dataset.shape, dataset.columns)
    # dataset check is there any null values
    # print(dataset.isnull().sum())

    # dividing target label and features
    X = dataset.drop(columns='target', axis=1)
    Y = dataset['target']
    #
    # split data into training and testing
    X_train, X_test, Y_train, Y_test = train_test_split(X, Y, test_size=0.1,
                                                        stratify=Y, random_state=2)
    # print(X.shape)
    # print(X_train.shape)
    # print(X_test.shape)
    #
    # apply our Logistic model because we have only two classes those are Mine and Rock
    # Model Training
    model = LogisticRegression()
    model.fit(X_train, Y_train)
    #
    # for production we will use pickle data for test scenorios
    dump(model, open('heart.pkl', 'wb'))
    #
    # Model Evaluation on training Data
    x_train_prediction = model.predict(X_train)
    train_data_accuracy = accuracy_score(x_train_prediction, Y_train)
    print("Training Accuracy", train_data_accuracy)

    # Model Evaluation on testing Data
    x_test_prediction = model.predict(X_test)
    test_data_accuracy = accuracy_score(x_test_prediction, Y_test)
    print("Test Accuracy", test_data_accuracy)
    #
    # input data prediction system
    # # input_data = [37,1,2,130,250,0,1,187,0,3.5,0,0,2] #1
    # input_data = [43,1,0,120,177,0,0,120,1,2.5,1,0,3] #0
    # array_input_data = np.asarray(input_data)
    # # reshape data
    # reshaped_data = array_input_data.reshape(1, -1)
    #
    # pred_val = model.predict(reshaped_data)
    # print(pred_val)


training_data()
