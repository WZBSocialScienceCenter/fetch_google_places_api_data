# Python scripts to fetch data from Google Places API

April 2020
Author: Markus Konrad <markus.konrad@wzb.eu>


## Installation

- you need Python 3.6 or newer (it's tested on Python 3.6)
- you need to install several packages via Python's package manager *pip*:


```
pip3 install -U pandas googlemaps xlrd
pip3 install --upgrade git+https://github.com/m-wrzr/populartimes
```

After that, create a file called `apikeys.py` in this directory with the sole content:

```
API_KEY = '...'
``` 

## Scripts

### places.py: Search for places of interest

#### Usage

Run as follows:

```
python3 places.py [old dataset specifier] [skip_queried_cities]
```

- arguments in square brackets are optional
- without any arguments, will create a new dataset in `data/pois` with format `<YEAR>-<MONTH>-<DAY>_h<HOUR>` according to current date and time; this is the *dataset specifier*
- you may pass such a dataset specifier as first argument
    - in this case, this existing data will be loaded and queries to existing places will be skipped
    - **helpful when running the script failed somewhere in between, but you don't want to start all over again**
- you may *additionally* add "`skip_queried_cities`" as argument
    - in this case, all already listed *ortsteile* in the old dataset will be completely skipped (no new search for these ortsteile) 

An example for loading and appending an existing dataset may be:

```
python3 places.py 2020-04-03_h13 skip_queried_cities
```

#### Internals

The script works as follows:

- (1) iterate through ortsteile; for each ortsteil:
    - (2) iterate through `PLACE_SEARCHES` (list of Google search queries); for each query:
        - (3) make a query to the Google Places API to find places according to query inside current ortsteil; will return up to 20 results; for each result place:
            - (4) try to fetch popularity values; if successfull, we found a "place of interest" (POI); store place details and its popularity values
        - repeat (3) for additional pages (depending on whether there are more pages and `page_limit` is not hit) 

Please note:

- no place will be queried for popularity twice in (4), e.g. if you "Super Mall" is found first for a query "mall", it will not be queried again for popularity when it is found e.g. for a query "shopping center"; it will only be stored under the first query
- same goes if the same place is found for different ortsteile; it will be queried for popularity only once and will only be stored for the first ortsteil for which it was found
- **this means you should not trust the "ortsteil" column in this respect!**   
 

#### Output

The script will create two datasets:

- `data/pois/<YEAR>-<MONTH>-<DAY>_h<HOUR>.csv` will contain all data about a "place of interest" (POI) with the following columns:
    - bezirk, key, ortsteil as from "ortsteile" dataset
    - lat, lng: geo-location (center) of the ortsteil
    - query: search query used to obtain the places
    - place_type: Google place type restriction if it was used
    - place_id: Google Place ID
    - name: place name
    - addr: place address
    - place_lat, place_lng: geo-location of the place
- `data/pois/<YEAR>-<MONTH>-<DAY>_h<HOUR>_pop.csv` will contain the current popularity data fetched for each place in the POI dataset with the following columns:
    - place_id: Google Place ID to link with POI dataset
    - local_date: local date at this place
    - local_weekday: local weekday from 0 – Monday to 6 – Sunday at this place
    - local_hour: local hour at this place
    - current_pop: current popularity at this place and local time
    - usual_pop: usual popularity at this place and local time


### generate_pois_full.py: Combine datasets from individual searches to a single file of unique places of interest

After running several searches with `places.py`, each creating a dataset of found places of interest in `data/pois`, this script can be used to combine these datasets, remove duplicates and store the result in `data/places_of_interest.csv`.

**The generated dataset will be used as input for periodic popularity queries via `popularity.py` script.**

#### Usage

Run as follows:

```
python3 generate_pois_full.py
```


### popularity.py: Periodically fetch popularity data for given places of interest

This script loads the places of interest in `data/places_of_interest.csv` and queries their place IDs for popularity data. The results are stored in `data/popularity/<DATE>_h<HOUR>.csv` with place ID, date, weekday, hour, current popularity and usual popularity.

The script is designed to be used as a hourly executed cronjob. You may define a schedule with constant `SCHEDULE` (line 15) of when to fetch the data. The script will abort when called outside of the defined schedule.   

#### Usage

Run as follows:

```
python3 popularity.py [force]
```

- append "force" argument to ignore the schedule and run at any time (used for testing)


### generate_popdata_full.py: Combine datasets with popularity values

After running several searches with `places.py`, each creating a dataset of popularity values for found places of interest in `data/pois` (suffix `_pop.csv`), this script can be used to combine these datasets together with the datasets that are generated when running `popularity.py` (with datasets in `data/popularity`). It will remove possible duplicates and store the result in `data/popularity.csv`.

#### Usage

Run as follows:

```
python3 generate_popdata_full.py
```

### places_interactive.py: Tools for interactively investigating search results

This file contains a few functions to interactively query the Maps search API. You can use it on the console.

For this, first install the "ipython" package:

```
pip3 install -U ipython
```

Then, start ipython:

```
ipython
```

First, import the functions and connect to the API:

```
from places_interactive import connect_api, make_query, print_results, save_results

connect_api()
```

Now you can query the API using `make_query()`. You can pass the following arguments:

1. search query
2. Google place type or `None` if you don't want to restrict to a certain place type
3. a tuple of geo coordinates as (lat, long)
4. search radius hint in meters
5. optional: return only currently opened places (default is `True`)

```
res = make_query('supermarket in Mitte, Berlin', None, (52.5372897,13.3602743), 10000)
```

To print results stored to a variable `res`, type:

```
print_results(res)
```

To save full results data stored in a variable `res` to a file `myplaces.csv`, type:

```
save_results(res, `myplaces.csv`)
```

The function will additionally return the saved dataframe.

Use up and down keys to browse through command history.

## Documentation for used Python packages

### googlemaps

- https://github.com/googlemaps/google-maps-services-python
- https://googlemaps.github.io/google-maps-services-python/docs/index.html

### populartimes

- https://github.com/m-wrzr/populartimes
