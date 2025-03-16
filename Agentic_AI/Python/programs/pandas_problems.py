import pandas as pd

# read csv
data1 = pd.read_csv('weather_data_cities.csv')
data2 = pd.read_csv('weather_data_cities.csv')

# get nulls
# print(data1['city'].isnull().sum())
# print(data1.isnull().sum())

# print(data1.isnull().values)

# print(data1.isnull().value_counts())

# print(data1['city'].isnull().value_counts())
# dropna()
data_dropna = data1.dropna()
# print(data_dropna)

# fillna()
data_fillna = data1.fillna('')
data_fillna1 = data1['city'].fillna('Hyd')

# print(data_fillna)
# print(data_fillna1)

# iloc & loc

print(data1.loc[:, ["city", 'temperature']])
print(data1.iloc[:5, [0, 1]])

print(data1[(data1['city'] == 'mumbai') & (data1['event'] == 'Rain')])
print(data1)
print('=================')
print(data1.loc[[0,1]])
print(data1.iloc[[0,1],[0,1]])

# apply, applymap & map
def sum(a):
    return a*2
print(data1['temperature'].apply(sum))
print(data1.apply(sum))
# map
print(data1['temperature'].map(sum))
print(data1.applymap(sum))

# merge
print(pd.merge(data1, data2.loc[1:5,:], on='temperature',how='outer', indicator=True))
print(pd.merge(data1, data2.loc[1:5,:], on='temperature',how='inner', indicator=True))

# sort_values
print(data1.sort_values(by='temperature', ascending=False))
print(data1.sort_values(by='temperature', ascending=True))


# concat
print(pd.concat([data1,data2], axis=0))
print(pd.concat([data1,data2], axis=0, ignore_index=True))
print(pd.concat([data1,data2], axis=1))
print(pd.concat([data1,data2], axis=0))

# set_index
print(data1.set_index('day')) # it will go into first column

#unique
print(data1['day'].unique())
# values_counts()
print(data1['day'].value_counts())

print(data1['day'].values)
#astype

# print(data1['windspeed'].astype(float))
print(data1['windspeed'].fillna(0).astype(int))
