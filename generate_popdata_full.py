import glob

import pandas as pd


RESULT_FILE = 'data/popularity.csv'

#%%

pois = pd.read_csv('data/places_of_interest.csv')

#%%

print('loading CSVs of regular popularity requests')

datasets = []
for csvfile in glob.glob('data/popularity/*.csv'):
    print('> loading', csvfile)
    datasets.append(pd.read_csv(csvfile))

print()

#%%

print('loading CSVs of initial popularity requests upon POI identification')

for csvfile in glob.glob('data/pois/*_pop.csv'):
    print('> loading', csvfile)
    datasets.append(pd.read_csv(csvfile))

print()

#%%

print('concatenating datasets')
full = pd.concat(datasets)\
    .sort_values(['local_date', 'local_hour'])\
    .drop_duplicates(['place_id', 'local_date', 'local_hour'])   # may have duplicates when "places.py" and "popularity.py" were run on the same date and hour

print('saving full dataset with %d rows to %s' % (len(full), RESULT_FILE))
full.to_csv(RESULT_FILE, index=False)

print('done.')
