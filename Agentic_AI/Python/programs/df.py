import pandas as pd
import numpy as np

df = pd.read_csv('C:\Repos\Agentic_AI\Python\programs\weather_data_cities.csv')
# df.loc[df[df['city']=='mumbai']['temperature'] > 10, 'temperature'] = 1
print(df)

data = df.loc[:5,:]

wind_data = df.loc[:2,:]['windspeed'].values.tolist()


def replace_func(data):
    data=data.replace('new york','york')
    return data

df.fillna('york', inplace=True)

data_df_str =  df['city'].apply(replace_func)

data_df_replace = df.replace({'new york':'york','mumbai':'bombay'})
df['city'] = df['city'].replace({'new york':'york','mumbai':'bombay'})

df_data_col_rename =  df.rename(columns={'city':'pattanam'})

df_drop_column = df.drop(columns=['city'])

# df['windspeed'] = [100 if i>50 else 0 for i in df['temperature']]
# print(df)