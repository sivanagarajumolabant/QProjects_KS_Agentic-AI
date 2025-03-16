import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from sklearn.linear_model import LogisticRegression
from pickle import dump


def training_data():
    dataset = pd.read_csv('creditcard.csv')
    # head data
    # print(dataset.head())
    # dataset shape
    # print(dataset.shape, dataset.columns)
    # dataset check is there any null values
    # print(dataset.isnull().sum())
    # print(dataset.groupby('Class').count())

    # labeling the data with same number
    legit = dataset[dataset.Class == 0]
    frad = dataset[dataset.Class == 1]
    # print(legit.shape)
    # print(frad.shape)
    # dividing target label and features
    legit = legit.sample(n=492)

    new_dataset = pd.concat([legit, frad], axis=0)

    X = new_dataset.drop(columns='Class', axis=1)
    Y = new_dataset['Class']

    # #
    # split data into training and testing
    X_train, X_test, Y_train, Y_test = train_test_split(X, Y, test_size=0.2,
                                                        stratify=Y, random_state=2)
    # # print(X.shape)
    # # print(X_train.shape)
    # # print(X_test.shape)
    # #
    # apply our Logistic model because we have only two classes those are Mine and Rock
    # Model Training
    model = LogisticRegression()
    model.fit(X_train, Y_train)
    #
    # for production we will use pickle data for test scenorios
    dump(model, open('credit.pkl', 'wb'))
    #
    # Model Evaluation on training Data
    x_train_prediction = model.predict(X_train)
    train_data_accuracy = accuracy_score(x_train_prediction, Y_train)
    print("Training Accuracy", train_data_accuracy)

    # Model Evaluation on testing Data
    x_test_prediction = model.predict(X_test)
    test_data_accuracy = accuracy_score(x_test_prediction, Y_test)
    print("Test Accuracy", test_data_accuracy)

    # input data prediction system
    # input_data = [37,1,2,130,250,0,1,187,0,3.5,0,0,2] #1
    input_data = [1, -0.966271712, -0.185226008, 1.79299334, -0.863291275, -0.01030888, 1.247203168, 0.23760894,
                  0.377435875, -1.387024063, -0.054951922, -0.226487264, 0.178228226, 0.50775687, -0.287923745,
                  -0.631418118, -1.059647245, -0.684092786, 1.965775003, -1.23262197, -0.208037781, -0.108300452,
                  0.005273597, -0.190320519, -1.175575332, 0.647376035, -0.221928844, 0.062722849, 0.061457629,
                  123.5]  # 0
    array_input_data = np.asarray(input_data)
    # reshape data
    reshaped_data = array_input_data.reshape(1, -1)

    pred_val = model.predict(reshaped_data)
    print(pred_val)


training_data()
