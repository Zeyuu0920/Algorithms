import pandas as pd
import numpy as np
import json

print('reading patterns...')

with pd.read_csv('patterns.csv', chunksize=10000, usecols=['postal_code', 'poi_cbg']) as reader:
  datalist = []
  for chunk in reader:
    datalist.append(chunk)
    
  df = pd.concat(datalist, axis=0)
  df['poi_cbg'] = df['poi_cbg'].astype('Int64').astype('str')
  df['postal_code'] = df['postal_code'].astype('str')

  del datalist

df = df.groupby('postal_code').agg(lambda x: list(np.unique(x))).reset_index()
df.set_index('postal_code', inplace=True)

dict_data = df.to_dict()

#dict_data = { i:list(set(j)) for i,j in dict_data.items() }

with open('zip_to_cbg.json', 'w') as f:
  json.dump(dict_data['poi_cbg'], f, indent=4)
