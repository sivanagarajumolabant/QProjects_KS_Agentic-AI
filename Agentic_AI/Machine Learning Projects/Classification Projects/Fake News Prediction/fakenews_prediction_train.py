import nltk
import pandas as pd
import re
import numpy as np
from nltk.corpus import stopwords
from sklearn.feature_extraction.text import TfidfVectorizer
from nltk.stem.porter import PorterStemmer
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from pickle import dump

nltk.download('stopwords')
ps = PorterStemmer()


def training():
    # read csv file using pandas
    dataset = pd.read_csv('train.csv')
    # print(dataset)

    # to get rows and columns
    # print(dataset.shape)

    # to check null values
    # print(dataset.isnull().sum())

    # to fill empty string where null values are there
    dataset = dataset.fillna('')

    # merge author and title columns
    dataset['Content'] = dataset['author'] + ' ' + dataset['title']
    # print(dataset['Content'])

    # apply preprocessing steps
    # apply stemming
    dataset['Content'] = dataset['Content'].apply(stemming)

    # dividing into target and features
    X = dataset['Content']
    Y = dataset['label']
    # print(X)
    # print(Y)

    # convert data for Text into numerical values
    tfidf_vector = TfidfVectorizer()
    tfidf_vector.fit(X)
    dump(tfidf_vector, open('fakenewsvector.pkl', 'wb'))
    X = tfidf_vector.transform(X)
    Y = dataset['label']
    # split into train and test data
    X_train, X_test, Y_train, Y_test = train_test_split(X, Y, test_size=0.2, stratify=Y, random_state=2)

    # model traing on training data
    model = LogisticRegression()
    model.fit(X_train, Y_train)
    dump(model, open('fakenewsmodel.pkl', 'wb'))
    train_pred_data = model.predict(X_train)
    accuracy_train = accuracy_score(train_pred_data, Y_train)
    print("Accuracy on Training Data ", accuracy_train)
    test_pred_data = model.predict(X_test)
    accuracy_test = accuracy_score(test_pred_data, Y_test)
    print("Accuracy on Test Data ", accuracy_test)

    # test the scenorio
    input_data = ["Consortiumnews.com Why the Truth Might Get You Fired"]
    # apply stemming
    input_array_data = [stemming(i) for i in input_data]

    # converting text into numeric
    # tfidf_vector = load(open('fakenewsvector.pkl', 'rb'))
    after_tfidf = tfidf_vector.transform(input_array_data)
    print(after_tfidf)

    # model = load(open('fakenewsmodel.pkl', 'rb'))
    model = model.predict(after_tfidf)
    print(model)


def stemming(data):
    data = re.sub(r'^[a-zA-Z]', ' ', data)
    data = data.lower()
    data = data.split()
    data_list = [ps.stem(i) for i in data if not i in stopwords.words('english')]
    data_str = ' '.join(data_list)
    return data_str


training()
