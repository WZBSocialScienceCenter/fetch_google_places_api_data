import sys
import os
from datetime import datetime

import pandas as pd
import populartimes

from apikeys import API_KEY

DATADIR = 'data/popularity'

# define schedule of when to run the script:
# dictionary keys are weekday codes from 0 (Monday) to 6 (Sunday)
# dictionary values are tuples of runtime hours
SCHEDULE = {
    1: (11, 15, 18),        # tuesday
    3: (10, 17, 21),        # thursday
    5: (14, 23),            # saturday
    6: (11, 16),            # sunday
}

#%% check whether to run script now

today = datetime.today()

force = len(sys.argv) > 1 and sys.argv[1] == 'force'

if force:
    print('will ignore runtime schedule')
else:
    sched_today = SCHEDULE.get(today.weekday(), [])
    if today.hour not in sched_today:
        print('script execution not scheduled for weekday %d and hour %d; will abort.' % (today.weekday(), today.hour))
        exit()


#%%

pois = pd.read_csv('data/places_of_interest.csv')
# pois = pois.sample(3)   # to test, sample only a few places

#%%

resultrows = []
n_queries = 0

for poi_i, (_, poirow) in enumerate(pois.iterrows()):
    print('place of interest %d/%d: %s / %s / %s' %
          (poi_i+1, len(pois), poirow.city, poirow.city_subunit, poirow.place_id))

    cought_exc = None
    now = datetime.now()
    try:
        n_queries += 1
        poptimes = populartimes.get_id(API_KEY, poirow.place_id)
    except Exception as exc:  # catch any exception
        poptimes = {}
        cought_exc = exc

    if 'current_popularity' in poptimes and 'populartimes' in poptimes:
        print('> got popularity data')

        resultrows.append([
            poirow.place_id,
            now.strftime('%Y-%m-%d'),
            now.weekday(),
            now.hour,
            poptimes['current_popularity'],
            poptimes['populartimes'][now.weekday()]['data'][now.hour]
        ])
    else:
        print('> failed to fetch popularity data')
        if cought_exc:
            print('>> exception:', cought_exc)

print('\n')

#%%

print('made %d queries and got %d results' % (n_queries, len(resultrows)))

if resultrows:
    popdata = pd.DataFrame(resultrows, columns=[
        'place_id',
        'local_date', 'local_weekday', 'local_hour',
        'current_pop', 'usual_pop'
    ])

    outfile = os.path.join(DATADIR, '%s_h%s.csv' % (today.strftime('%Y-%m-%d'), str(today.hour).zfill(2)))
    print('saving data to file', outfile)
    popdata.to_csv(outfile, index=False)
else:
    print('nothing to save')

print('done.')
