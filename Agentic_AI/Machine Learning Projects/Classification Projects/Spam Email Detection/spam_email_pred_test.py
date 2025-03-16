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


def testing():
    # input data prediction
    input_data = [
        "SIX chances to win CASH! From 100 to 20,000 pounds txt> CSH11 and send to 87575. Cost 150p/day, 6days, 16+ TsandCs apply Reply HL 4 info"]
    model = load(open('spammodel.pkl', 'rb'))
    tfidf_vector = load(open('spamvector.pkl', 'rb'))
    tfidf_data = tfidf_vector.transform(input_data)
    # array_data = np.asarray(tfidf_data)
    # reshaped_data = array_data.reshape(1,-1)
    pred = model.predict(tfidf_data)
    print(pred)


testing()
