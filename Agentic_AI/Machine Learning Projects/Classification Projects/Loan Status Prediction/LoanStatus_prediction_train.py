import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from sklearn import svm
from pickle import dump


def training_data():
    dataset = pd.read_csv('train.csv')
    # print(dataset.isnull().sum())
    # pre processing steps
    dataset = dataset.dropna()
    # print(dataset.isnull().sum())
    # print(dataset.shape)

    # replaced with the values
    # print(dataset.head())
    # print(dataset.columns)
    # print(dataset['Dependents'].value_counts())
    dataset.replace({"Self_Employed": {'Yes': 1, 'No': 0}, "Dependents": {'3+': 3}, "Loan_Status": {'Y': 1, 'N': 0},
                     "Property_Area": {'Semiurban': 0, 'Urban': 1, 'Rural': 2},
                     "Gender": {'Male': 0, 'Female': 1}, "Education": {'Graduate': 0, 'Not Graduate': 1},
                     "Married": {'Yes': 0, 'No': 1}}, inplace=True)
    # print(dataset)
    # diving into target and faetures
    X = dataset.drop(columns=['Loan_ID', 'Loan_Status'])
    Y = dataset['Loan_Status']
    # print(X,Y)

    # split data into training and testing
    X_train, X_test, Y_train, Y_test = train_test_split(X, Y, test_size=0.1,
                                                        stratify=Y, random_state=2)
    # print(X.shape)
    # print(X_train.shape)
    # print(X_test.shape)

    # apply model
    model = svm.SVC(kernel='linear')
    model.fit(X_train, Y_train)
    dump(model, open('loanmodel.pkl', 'wb'))
    # accu traing data
    train_pre = model.predict(X_train)
    accuracy_train = accuracy_score(train_pre, Y_train)
    print("Accuracy Training score ", accuracy_train)

    # accu test data
    test_pre = model.predict(X_test)
    accuracy_test = accuracy_score(test_pre, Y_test)
    print("Accuracy Testing score ", accuracy_test)

    # make predictive system
    # input_data = [0, 0, 3, 0, 0, 3036, 2504, 158, 360, 0, 0]
    input_data = [0, 0, 1, 0, 0, 4583, 1508, 128, 360, 1, 2]
    array_input_data = np.asarray(input_data)
    # reshape data
    reshaped_data = array_input_data.reshape(1, -1)

    pred_val = model.predict(reshaped_data)
    print(pred_val)


training_data()
