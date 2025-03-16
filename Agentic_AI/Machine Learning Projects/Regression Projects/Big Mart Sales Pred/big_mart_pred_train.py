import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn import metrics
from xgboost import XGBRegressor
from sklearn.preprocessing import LabelEncoder
from pickle import dump, load

encoder = LabelEncoder()


def train():
    dataset = pd.read_csv('Train.csv')
    # print(dataset)

    # checking for missing values
    # dataset.isnull().sum()

    # print(dataset['Item_Weight'].mean())
    dataset['Item_Weight'].fillna(dataset['Item_Weight'].mean(), inplace=True)
    # mode of "Outlet_Size" column
    # print(dataset['Outlet_Size'].mode())

    mode_col = dataset.pivot_table(values='Outlet_Size', columns='Outlet_Type', aggfunc=(lambda x: x.mode()[0]))
    miss_val = dataset['Outlet_Size'].isnull()

    dataset.loc[miss_val, 'Outlet_Size'] = dataset.loc[miss_val, 'Outlet_Type'].apply(lambda x: mode_col[x])

    # print(dataset.isnull().sum())
    dataset.replace({'Item_Fat_Content': {'low fat': 'Low Fat', 'LF': 'Low Fat', 'reg': 'Regular'}}, inplace=True)

    dataset['Item_Identifier'] = encoder.fit_transform(dataset['Item_Identifier'])

    dataset['Item_Fat_Content'] = encoder.fit_transform(dataset['Item_Fat_Content'])

    dataset['Item_Type'] = encoder.fit_transform(dataset['Item_Type'])

    dataset['Outlet_Identifier'] = encoder.fit_transform(dataset['Outlet_Identifier'])

    dataset['Outlet_Size'] = encoder.fit_transform(dataset['Outlet_Size'])

    dataset['Outlet_Location_Type'] = encoder.fit_transform(dataset['Outlet_Location_Type'])

    dataset['Outlet_Type'] = encoder.fit_transform(dataset['Outlet_Type'])

    X = dataset.drop(columns='Item_Outlet_Sales', axis=1)
    Y = dataset['Item_Outlet_Sales']
    X_train, X_test, Y_train, Y_test = train_test_split(X, Y, test_size=0.2, random_state=2)

    model = XGBRegressor()
    model.fit(X_train, Y_train)
    dump(model, open('bigmodel.pkl', 'wb'))

    # prediction on training data
    training_data_prediction = model.predict(X_train)
    accuracy_train = metrics.r2_score(Y_train, training_data_prediction)
    print(accuracy_train)

    # prediction on Test data
    test_data_prediction = model.predict(X_test)
    accuracy_test = metrics.r2_score(Y_test, test_data_prediction)
    print(accuracy_test)


    # input system
    # input_data = ('FDA15',9.3,'Low Fat',0.016047301,'Dairy',249.8092,'OUT049',1999,'Medium','Tier 1','Supermarket Type1')
    input_data = ('FDP36',10.395,'Regular',0,'Baking Goods',51.4008,'OUT018',2009,'Medium','Tier 3','Supermarket Type2')
    enc = encoder.fit_transform(input_data)
    array_data = np.asarray(enc)
    reshaped_data = array_data.reshape(1,-1)
    val = model.predict(reshaped_data)
    print(val)

train()
