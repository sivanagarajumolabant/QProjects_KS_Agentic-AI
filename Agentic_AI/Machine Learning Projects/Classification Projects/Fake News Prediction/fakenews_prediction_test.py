import reg
import numpy as np
import nltk
from nltk.corpus import stopwords
from sklearn.feature_extraction.text import TfidfVectorizer
from nltk.stem.porter import PorterStemmer
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from pickle import load

nltk.download('stopwords')
ps = PorterStemmer()


def stemming(data):
    data = re.sub(r'^[a-zA-Z]', ' ', data)
    data = data.lower()
    data = data.split()
    data_list = [ps.stem(i) for i in data if not i in stopwords.words('english')]
    data_str = ' '.join(data_list)
    return data_str


def testing():
    # test the scenorio
    input_data = ["The Doc 100 oz Sunshine Silver Bars Just $0.29/oz Over Spot ANY QTY!"]
    # apply stemming
    input_array_data = [stemming(i) for i in input_data]

    # converting text into numeric
    tfidf_vector =load(open('fakenewsvector.pkl','rb'))
    after_tfidf = tfidf_vector.transform(input_array_data)
    print(after_tfidf)

    model= load(open('fakenewsmodel.pkl','rb'))
    model = model.predict(after_tfidf)
    print(model)


testing()
