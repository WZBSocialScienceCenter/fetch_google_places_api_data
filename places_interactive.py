import googlemaps
import pandas as pd

from apikeys import API_KEY

#%%

gmaps = None


def connect_api():
    global gmaps
    gmaps = googlemaps.Client(key=API_KEY)


def make_query(query, place_type, location, radius, **kwargs):
    assert isinstance(query, str)
    assert place_type is None or isinstance(place_type, str)
    assert isinstance(location, (tuple, list)) and len(location) == 2

    return gmaps.places(query=query, location=location, radius=radius,
                        type=place_type, **kwargs)


def print_results(places):
    if places['status'] != 'OK':
        print('bad status: %s' % places['status'])
        return

    print('%d results:' % len(places['results']))

    for i, p in enumerate(places['results']):
        print('%d/%d: %s in %s' % (i+1, len(places['results']), p['name'], p.get('formatted_address', '<unknown>')))

    print()

    if 'next_page_token' in places:
        print('got at least one more page of results')

    print()


def save_results(places, filepath):
    if places['status'] != 'OK':
        print('bad status: %s' % places['status'])
        return

    resultrows = []
    for p in places['results']:
        resultrows.append([
            p['place_id'],
            p['name'],
            p.get('formatted_address', ''),
            p['geometry']['location']['lat'],
            p['geometry']['location']['lng']
        ])

    df = pd.DataFrame(resultrows, columns=['place_id', 'name', 'addr', 'place_lat', 'place_lng'])
    df.to_csv(filepath, index=False)

    print('saved data to', filepath)

    return df
