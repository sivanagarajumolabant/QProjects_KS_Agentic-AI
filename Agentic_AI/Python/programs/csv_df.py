import pandas as pd
import numpy as np

# Sample data
data = [
    [1, 2, 3, 4, 5],
    [1, 2, 3],
    [4],
    [1, 2, 3, 4, 5, 6, None, 7]
]

df = pd.DataFrame(data, columns=['col1', 'col2', 'col3', 'col4', 'col5', 'col6', 'col7', 'col8'])
df.to_csv('csv_df.csv', index=False)
df = pd.read_csv('csv_df.csv')

columns = ['col1', 'col2', 'col3', 'col4', 'col5']

print(df)
if len(df.columns) > len(columns):
    df = df.iloc[:, [0,1]]
print(df)
