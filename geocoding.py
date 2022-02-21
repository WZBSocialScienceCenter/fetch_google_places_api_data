"""
Geocoding for Berlin "Ortsteile".

Find geo-location (center) of each Ortsteil using Google Maps Geocode API.
"""

import pandas as pd
pd.set_option('display.max_columns', 100)
pd.set_option('display.width', 180)

import googlemaps

from apikeys import API_KEY


RESULT_FILE = 'data/cities.csv'

#%%

gmaps = googlemaps.Client(key=API_KEY)

#%%

cities = pd.read_csv(RESULT_FILE)
cities_geocode = cities.loc[cities.lat.isna() | cities.lng.isna(),].copy()

print('will geocode %d places' % (len(cities_geocode)))

resultrows = []
for idx, row in cities_geocode.iterrows():

    if pd.isna(row.city_subunit):
        query = row.city
    else:
        query = row.city_subunit + ', ' + row.city

    print('> query:', query)
    res = gmaps.geocode(query, region='de')

    loc = None
    if res and len(res) > 0:
        item = res[0]
        if 'geometry' in item:
            loc = item['geometry']['location']

    if loc is None:
        print('>> geocoding failed')
    else:
        print('>> geocoding successful')

        resultrows.append([
            idx,
            loc['lat'],
            loc['lng'],
        ])

print()

#%%

print('geocoding successful for %d of %d places' % (len(resultrows), len(cities_geocode)))

print('will save result to', RESULT_FILE)
georesults = pd.DataFrame(resultrows, columns=['idx', 'lat', 'lng']).set_index('idx')
cities.update(georesults)

cities.to_csv(RESULT_FILE, index=False)

print('done.')
