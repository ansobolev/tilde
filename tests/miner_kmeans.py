#!/usr/bin/env python

# example of data-mining on band gaps and periodic table element groups
# using k-means as implemented in scikit-learn
# v080514

import sys
import os
import math
import json
import time

starttime = time.time() # benchmarking

from sklearn.cluster import KMeans

sys.path.insert(0, os.path.realpath(os.path.dirname(os.path.abspath(__file__)) + '/../'))
from core.settings import settings, connect_database, check_db_version

sys.path.insert(0, os.path.realpath(os.path.dirname(os.path.abspath(__file__)) + '/../core/deps'))
from ase.data import chemical_symbols

from pymatgen.core.periodic_table import Element


db_choice = None
if settings['db']['type'] == 'sqlite':
    try: db_choice = sys.argv[1]
    except IndexError: sys.exit('No DB name defined!')
    
db = connect_database(settings, db_choice)
if not db: sys.exit('Connection to DB failed!')

# check DB_SCHEMA_VERSION
incompatible = check_db_version(db)
if incompatible:
    sys.exit('Sorry, database ' + workpath + ' is incompatible.')

# ^^^ the obligatory code above, the actual procedures of interest below VVV

cursor = db.cursor()
sql = 'SELECT info FROM results WHERE checksum IN (SELECT checksum FROM tags g INNER JOIN topics s ON g.tid=s.tid WHERE s.categ=6 AND s.topic=%s)' % settings['ph']
try: cursor.execute( sql, ('electron structure',) ) # 6 is calctype# to guarantee *bandgap* presence
except: sys.exit('Fatal error: ' + "%s" % sys.exc_info()[1])

data = []
ref = []

while 1:
    row = cursor.fetchone()
    if not row: break
    item = json.loads(row[0])
    
    if item['nelem'] != 2: continue # only binary compounds!
    
    if not 'bandgap' in item: sys.exit('DB contains no needed info!')
    
    if 0 < item['bandgap'] < 15: a = [item['bandgap']]
    else: continue # avoid metals and non-physical things

    i=0
    occured_elems = []
    while 1:
        try: item['element'+str(i)]
        except KeyError: break
        if Element.is_valid_symbol(item['element'+str(i)]):
            e = Element(item['element'+str(i)])
            if e.is_lanthanoid or e.is_actinoid: group = 3
            else: group = e.group
        else: sys.exit('Undefined element: '+item['element'+str(i)])

        occured_elems.append(group)        
        i+=1
    occured_elems.sort()
    a.extend(occured_elems)
    data.append(a)
    
    ref.append({'standard':item['standard'], 'bandgap': item['bandgap']})

if not data: sys.exit('DB contents do not satisfy the criteria!')

kmeans = KMeans(n_clusters=10)
kmeans.fit(data)

# sorting
clusters = {}
for n, i in enumerate(kmeans.labels_):
    try: clusters[i].append(ref[n])
    except KeyError: clusters[i] = [ ref[n] ]

for k, v in clusters.iteritems():
    print "-"*100
    print 'Cluster', (k+1)
    print "-"*100
    
    formulae_gaps = {}
    for i in v:
        try: formulae_gaps[i['standard']].append(i['bandgap'])
        except KeyError: formulae_gaps[i['standard']] = [ i['bandgap'] ]
        #print "\t", i['standard'], i['bandgap']
    for kk, vv in formulae_gaps.iteritems():
        print "\t", kk, min(vv), "----", max(vv), "eV"
    
print "Done in %1.2f sc" % (time.time() - starttime)
