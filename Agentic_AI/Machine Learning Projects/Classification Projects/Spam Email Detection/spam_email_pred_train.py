import nltk
import pandas as pd
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
    dataset = pd.read_csv('mail_data.csv')
    # print(dataset)
    # print(dataset.isnull().sum())
    # dataset['Category'].fillna('')
    dataset = dataset.where(pd.notnull(dataset), '')
    #
    # print(dataset.groupby('Category').count())
    dataset.replace({"Category": {"ham": 1, "spam": 0}}, inplace=True)
    # print(dataset)

    # divide the features and target
    X = dataset['Message']
    Y = dataset['Category']

    # convert text to numric data
    tfidf_vector = TfidfVectorizer(min_df=1, lowercase=True, stop_words='english')
    tfidf_vector.fit(X)
    dump(tfidf_vector, open('spamvector.pkl', 'wb'))
    converted_data = tfidf_vector.transform(X)
    X = converted_data
    Y = dataset['Category']

    # split data into two parts
    X_train, X_test, Y_train, Y_test = train_test_split(X, Y, stratify=Y, test_size=0.2, random_state=3)

    # apply model
    model = LogisticRegression()
    model.fit(X_train, Y_train)
    dump(model, open('spammodel.pkl', 'wb'))

    # predict on training data and accuracy score
    x_train_pred = model.predict(X_train)
    acc_x_train = accuracy_score(x_train_pred, Y_train)
    print("accuracy on Training data", acc_x_train)

    # predict on testing data and accuracy score
    x_test_pred = model.predict(X_test)
    acc_x_test = accuracy_score(x_test_pred, Y_test)
    print("accuracy on testing data", acc_x_test)

    # input data prediction
    input_data = ["Dear 0776xxxxxxx U've been invited to XCHAT. This is our final attempt to contact u! Txt CHAT to 86688 150p/MsgrcvdHG/Suite342/2Lands/Row/W1J6HL LDN 18yrs"]
    tfidf_data = tfidf_vector.transform(input_data)
    array_data = np.asarray(tfidf_data)
    # reshaped_data = array_data.reshape(1,-1)
    pred = model.predict(tfidf_data)
    print(pred)


training()
