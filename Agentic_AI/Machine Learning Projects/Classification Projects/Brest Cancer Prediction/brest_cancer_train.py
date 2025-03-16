import nltk
import pandas as pd
import sklearn.datasets
import reg
import numpy as np
from nltk.corpus import stopwords
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from pickle import dump


def training():
    # read csv file using pandas
    cancer_dataset = sklearn.datasets.load_breast_cancer()
    feature_data =  pd.DataFrame(cancer_dataset.data, columns=cancer_dataset.feature_names)
    # print(feature_data.columns)

    target_data  = pd.DataFrame(cancer_dataset.target)
    target_data.rename(columns={0:'Label'}, inplace=True)
    # print(target_data)

    dataset = pd.concat([feature_data,target_data], axis=1)
    # print(dataset[:].values)
    # print(dataset.loc[1,:])

    # dividing features
    X =  dataset.drop(columns='Label')
    Y = dataset['Label']
    # print(X)

    # divinding train and test split
    # split data into two parts
    X_train, X_test, Y_train, Y_test = train_test_split(X, Y, test_size=0.2, random_state=2)

    # apply model
    model = LogisticRegression()
    model.fit(X_train, Y_train)
    dump(model, open('brestcancermodel.pkl', 'wb'))

    # predict on training data and accuracy score
    x_train_pred = model.predict(X_train)
    acc_x_train = accuracy_score(x_train_pred, Y_train)
    print("accuracy on Training data", acc_x_train)

    # predict on testing data and accuracy score
    x_test_pred = model.predict(X_test)
    acc_x_test = accuracy_score(x_test_pred, Y_test)
    print("accuracy on testing data", acc_x_test)

    # input data prediction
    input_data = [13.54,14.36,87.46,566.3,0.09779,0.08129,0.06664,0.04781,0.1885,0.05766,0.2699,0.7886,2.058,23.56,0.008462,0.0146,0.02387,0.01315,0.0198,0.0023,15.11,19.26,99.7,711.2,0.144,0.1773,0.239,0.1288,0.2977,0.07259]

    array_data = np.asarray(input_data)
    reshaped_data = array_data.reshape(1,-1)
    pred = model.predict(reshaped_data)
    print(pred)

training()
