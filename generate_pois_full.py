import glob
import os
from datetime import datetime

import pandas as pd

RESULT_FILE = 'data/places_of_interest.csv'

#%%

print('will load collected POI CSV files')

datasets = []
for csvfile in sorted(glob.glob('data/pois/*.csv')):
    if not csvfile.endswith('_pop.csv'):
        print('loading', csvfile)

        df = pd.read_csv(csvfile)
        filedate = datetime.strptime(os.path.basename(csvfile)[:10], '%Y-%m-%d')

        if filedate <= datetime(2020, 4, 9):   # old format that only contains Berlin data
            df['city'] = 'Berlin'
            df['city_subunit'] = df['ortsteil']

            for col in ('bezirk' ,'key' , 'ortsteil'):
                del df[col]

        datasets.append(df)

print('loaded %d datasets with %d rows in total' % (len(datasets), sum(map(len, datasets))))

#%%

print('concatenating datasets')
full = pd.concat(datasets)\
    .sort_values(['place_id', 'place_type'])\
    .drop_duplicates('place_id', keep='first')\
    .sort_values(['city', 'city_subunit', 'query', 'name'])\
    .reset_index(drop=True)

print('full dataset has %d POIs' % len(full))

print('saving data to file', RESULT_FILE)
full[['city', 'city_subunit', 'lat', 'lng' , 'query', 'place_type', 'place_id',
      'name', 'addr', 'place_lat', 'place_lng']].to_csv(RESULT_FILE, index=False)
