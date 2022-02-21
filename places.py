import os
import sys
from datetime import datetime

import pandas as pd
import googlemaps
import populartimes

from apikeys import API_KEY

pd.set_option('display.max_columns', 100)
pd.set_option('display.width', 180)

#%%

# fill in search queries

PLACE_SEARCHES_LOCALLY = [
   'Supermarkt',
   'Tankstelle',
   'Drogeriemarkt',
   'Fast food',
   # 'Mode',
]

PLACE_SEARCHES_CITYWIDE = [
   'Parks',
   # 'Platz',
   'Bahnhöfe',
   'Haltestellen',
   'Sehenswürdigkeiten',
   'Baumarkt',
   'Elektronikmarkt',
   'shopping center'
]

PLACE_SEARCHES_FORCE = {     # always use these queries no matter if we already had that city
    # 'Mode',
    # 'Elektronikmarkt',
}

PLACE_SEARCHES_RESTRICT_OPEN_NOW = {   # only queries in this set will use "open_now" restriction
    #'shopping centre',
   # 'street market',
}

POIS_FILE ='data/places_of_interest.csv'    # full dataset of unique places (from generate_pois_full.py)
CITIES_FILE = 'data/cities.csv'

RESULT_FILE = 'data/pois/%s.csv'
RESULT_POP_FILE = 'data/pois/%s_pop.csv'
QUERIED_FILE = 'data/places_of_interest_queried_cities.pickle'

#%% functions


def run_query(queried_cities, existing_place_ids, pages_limit, t_start_ymdh, place_query,
              search_location, search_radius, open_now, city, city_subunit):
    if pd.isna(city_subunit):
        city_subunit = ''

    query_id = t_start_ymdh + city + city_subunit + place_query
    if query_id in queried_cities:
        print('>> skipping (already queried this city/city_subunit for this kind of places)')
        return

    if city_subunit:
        full_query = place_query + ' in ' + city_subunit + ', ' + city
    else:
        full_query = place_query + ' in ' + city

    if open_now is not None:
        open_now_info = '(open now restriction: ' + str(open_now) + ')'
    else:
        open_now_info = ''

    assert len(search_location) == 2

    print('>> query: "%s" %s around lat=%.4f, lng=%.4f' % (full_query, open_now_info,
                                                           search_location[0], search_location[1]))

    n_pois = 0
    i_page = 1
    next_page_token = ''
    found_places = []
    found_places_pop = []
    while next_page_token is not None:
        print('>>> page', i_page, '/', pages_limit)

        kwargs = {}
        if next_page_token:
            kwargs['page_token'] = next_page_token
        if open_now is not None:
            kwargs['open_now'] = open_now

        now = datetime.now()

        places = gmaps.places(query=full_query, location=search_location, radius=search_radius, **kwargs)
        # places = {   # test data
        #     'status': 'OK',
        #     'results': [
        #         {
        #             'name': 'Test place',
        #             'place_id': 'test placeid',
        #             'geometry': {
        #                 'location': {
        #                     'lat': 1.0,
        #                     'lng': 2.0,
        #                 }
        #             }
        #         }
        #     ]
        # }

        if places['status'] != 'OK':
            print('>>> skipping (bad status: %s)' % places['status'])
            next_page_token = None
            continue

        print('>>> got %d results' % len(places['results']))

        if i_page >= pages_limit:
            next_page_token = None
        else:
            next_page_token = places.get('next_page_token', None)
        queried_cities.append(query_id)

        for i_place, place in enumerate(places['results']):
            print('>>>> place %d/%d: %s' % (i_place + 1, len(places['results']), place['name']))

            if place['place_id'] in existing_place_ids:
                print('>>>> skipping (already queried place with ID %s)' % place['place_id'])
                continue

            poptimes = populartimes.get_id(api_key=API_KEY, place_id=place['place_id'])
            # poptimes = {  # test data
            #     'current_popularity': 40,
            #     'populartimes': {
            #         3: {
            #             'data': {
            #                 17: 60,
            #             }
            #         }
            #     }
            # }

            if 'current_popularity' in poptimes and 'populartimes' in poptimes:
                print('>>>> adding this place as place of interest')

                found_places.append([
                    city,
                    city_subunit,
                    search_location[0],
                    search_location[1],
                    place_query,
                    ','.join(place.get('types', [])),
                    place['place_id'],
                    place['name'],
                    place.get('formatted_address', ''),
                    place['geometry']['location']['lat'],
                    place['geometry']['location']['lng']
                ])

                poi_localwd = now.weekday()
                poi_localhour = now.hour

                found_places_pop.append([
                    place['place_id'],
                    now.strftime('%Y-%m-%d'),
                    poi_localwd,
                    poi_localhour,
                    poptimes['current_popularity'],
                    poptimes['populartimes'][poi_localwd]['data'][poi_localhour]
                ])

                existing_place_ids.add(place['place_id'])
                n_pois += 1

        i_page += 1

    print('>>> got %d places of interest for this query in this area' % n_pois)

    return found_places, found_places_pop


def store_data(resultrows, resultrows_pop, existing_pois, result_file, result_pop_file):
    print('preparing and storing dataset')

    places_of_interest = pd.DataFrame(resultrows, columns=[
        'city', 'city_subunit', 'lat', 'lng',
        'query', 'place_type', 'place_id', 'name', 'addr', 'place_lat', 'place_lng'
    ])

    if existing_pois is not None:
        places_of_interest = pd.concat((existing_pois, places_of_interest), ignore_index=True)

    places_of_interest = places_of_interest \
        .drop_duplicates(['city', 'city_subunit', 'query', 'place_id'])\
        .sort_values(by=['city', 'city_subunit', 'query', 'name'])\
        .reset_index(drop=True)

    print('got %d places of interest so far' % len(places_of_interest))

    print('storing places of interest to file', result_file)
    places_of_interest.to_csv(result_file, index=False)

    print('storing initial popularity data for places of interest to file', result_pop_file)
    poi_popdata = pd.DataFrame(resultrows_pop, columns=['place_id',
                                                        'local_date', 'local_weekday', 'local_hour',
                                                        'current_pop', 'usual_pop'])
    poi_popdata.to_csv(result_pop_file, index=False)


#%% script start

t_start_ymdh = datetime.now().strftime('%Y-%m-%d_h%H')

if len(sys.argv) >= 2:
    query_only_cities = pd.read_csv(sys.argv[1])

    print('will only query %d cities loaded from %s' % (len(query_only_cities), sys.argv[1]))
else:
    query_only_cities = None

result_file = RESULT_FILE % t_start_ymdh
result_pop_file = RESULT_POP_FILE % t_start_ymdh

#%%

gmaps = googlemaps.Client(key=API_KEY)

cities = pd.read_csv('data/cities.csv').sample(frac=1).reset_index(drop=True)  # additionally shuffle rows
#cities = cities[cities.city.isin({'Bremen', 'Dresden'})]
#cities = cities[cities.city_subunit.isin({'Malchow'})]

if query_only_cities is not None:
    query_only_cities['id'] = query_only_cities.city.str.cat(query_only_cities.city_subunit.fillna(''))
    cities['id'] = cities.city.str.cat(cities.city_subunit.fillna(''))
    filter_ids = set(query_only_cities.id.to_list())
    cities = cities[cities.id.isin(filter_ids)].reset_index(drop=True)
    assert len(cities) == len(filter_ids), 'all requested cities must exist in cities.csv dataset'

if os.path.exists(result_file):
    print('loading existing POI CSV file', result_file)
    existing_pois = pd.read_csv(result_file)
    existing_place_ids = set(existing_pois.place_id)
    print('> %d existing places' % len(existing_place_ids))
    existing_queried_cities = set(existing_pois.city.str.cat(existing_pois.city_subunit))
    print('> %d existing cities' % len(existing_queried_cities))
else:
    existing_pois = None
    existing_place_ids = set()
    existing_queried_cities = set()

if os.path.exists(result_pop_file):
    print('loading existing POI initial popularity score CSV file', result_pop_file)
    existing_popdata = pd.read_csv(result_pop_file)
    resultrows_pop = list(map(lambda tup: tup[1].to_list(), existing_popdata.iterrows()))
    print('> %d existing place popularity score entries' % len(resultrows_pop))
else:
    resultrows_pop = []


queried_cities = []

#%% run searches

resultrows = []

print('searching for places ...')

for city_i, cityrow in cities.iterrows():
    citywide = pd.isna(cityrow.city_subunit)

    print('> city %d/%d: %s / %s' % (city_i+1, len(cities), cityrow.city, cityrow.city_subunit))

    assert not pd.isna(cityrow.lat) and not pd.isna(cityrow.lng), 'geo locations must be given'

    if citywide:
        citycheck = cityrow.city
        onlycitywide = sum(cities.city == cityrow.city) == 1
    else:
        citycheck = cityrow.city + cityrow.city_subunit
        onlycitywide = False

    if onlycitywide:
        queries = PLACE_SEARCHES_CITYWIDE + PLACE_SEARCHES_LOCALLY
    else:
        queries = PLACE_SEARCHES_CITYWIDE if citywide else PLACE_SEARCHES_LOCALLY

    if query_only_cities is not None and sum(query_only_cities.id == citycheck) == 1:
        all_queries = bool(query_only_cities[query_only_cities.id == citycheck].iloc[0].all_queries)
    else:
        all_queries = True

    for place_query in queries:
        if (not all_queries and place_query not in PLACE_SEARCHES_FORCE) or citycheck in existing_queried_cities:
            print('> skipping (already queried this city / subunit)')
            continue

        found_places, found_places_pop = run_query(queried_cities, existing_place_ids, cityrow.pages_limit,
                                                   t_start_ymdh, place_query, (cityrow.lat, cityrow.lng),
                                                   cityrow.place_search_radius,
                                                   True if place_query in PLACE_SEARCHES_RESTRICT_OPEN_NOW else None,
                                                   cityrow.city, cityrow.city_subunit)
        resultrows.extend(found_places)
        resultrows_pop.extend(found_places_pop)

    store_data(resultrows, resultrows_pop, existing_pois, result_file, result_pop_file)
    print('\n')


print('done.')
