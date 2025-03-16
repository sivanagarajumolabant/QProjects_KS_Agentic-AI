import pandas as pd

data1  =pd.read_csv('C:\Repos\Agentic_AI\Python\programs\weather_data_cities.csv')
data2  =pd.read_csv('C:\Repos\Agentic_AI\Python\programs\weather_data_cities.csv')

data2.drop(index=[10,11], inplace=True)

# print()
# apply_data = data1['temperature'].apply(lambda x:x+1)
# print(apply_data)

merge_data = pd.merge(data1,data2, how='outer', indicator=True)
merge_data.rename(columns={"_merge":"merge"},inplace=True)
print(merge_data)
left_data = merge_data[merge_data['merge']=='left_only']
right_data = merge_data[merge_data['merge']=='right_only']
both_data = merge_data[merge_data['merge']=='both']

# print(left_data)
right_data['merge']='data2'
left_data['merge']='data1'



total_df = pd.concat([both_data,left_data, right_data], axis=0)
print(total_df)