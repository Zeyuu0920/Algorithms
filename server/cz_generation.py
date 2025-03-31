import pandas as pd
import geopandas as gpd
import networkx as nx
import json
from pyzipcode import ZipCodeDatabase

# CONSTANTS (need to be changed)
location_name = 'baltimore'
states = [ 'MD', 'PA', 'MN', 'WI', 'AK', 'OK', 'NY', 'NJ' ]

zcdb = ZipCodeDatabase()

zip_codes = sum([ [ int(z.zip) for z in zcdb.find_zip(state=state) ] for state in states ], [])

# Initialize gdf
gdf1 = gpd.read_file('tl_2010_24_bg10/tl_2010_24_bg10.shp')
gdf2 = gpd.read_file('tl_2010_42_bg10/tl_2010_42_bg10.shp')
gdf3 = gpd.read_file('tl_2010_40_bg10/tl_2010_40_bg10.shp')
gdf = gpd.GeoDataFrame(pd.concat([gdf1, gdf2, gdf3], ignore_index=True))

#Read safegraph files
filename = location_name + '.csv'

print('reading patterns!')

try:
  df = pd.read_csv(filename)
except:
  datalist = []

  with pd.read_csv('patterns.csv', chunksize=10000) as reader:
    for chunk in reader:
      datalist.append(chunk[chunk['postal_code'].isin(zip_codes)])

  df = pd.concat(datalist, axis=0)
  del datalist

  try:
    df['poi_cbg'] = df['poi_cbg'].astype('int64')
  except:
    print(df['poi_cbg'])

  df.to_csv(filename)

print('read patterns!')

#Try to avoid this function especially in loops since it takes time
def cbg_geocode(cbg_code):

    cbg_row = gdf[gdf['GEOID10'] == cbg_code]
    
    # Check if a match was found
    if not cbg_row.empty:
        # Get the centroid of the matched geometry
        centroid = cbg_row.geometry.centroid.iloc[0]
        return centroid.y, centroid.x  # Return latitude, longitude
    else:
        print(f"CBG code {cbg_code} not found in the data.")
        return None

#function to find distances between cbgs, used in the distance graph
from math import sin, cos, atan2, pi, sqrt
def distance(lat1, long1, lat2, long2):
    lat1 = lat1*pi/180
    long1 = long1*pi/180
    lat2 = lat2*pi/180
    long2 = long2*pi/180

    Radius = 6371
    haversine = sin((lat2-lat1)/2)**2 + cos(lat1)*cos(lat2) * sin((long2-long1)/2)**2
    c = 2*atan2(sqrt(haversine), sqrt(1-haversine))
    dist = Radius*c
    return dist
  
def gen_graph(df, weighted=True):
    """
    Reads from a SafeGraph dataframe of a certain location.

    Args:
        df (pd.DataFrame): The SafeGraph dataset of a particular location.
        weighted (bool, optional): Whether the result should have weighted edges. Defaults to True.

    Returns:
        nx.Graph: Graph where nodes are the CBGs, and edges and weights are determined by visitor interactions.
    """
    G = nx.Graph()
    regg_count = 0  # Counter for rows with errors
    
    for _, row in df.iterrows():
      # Extract and process 'poi_cbg'
      poi_cbg = str(row['poi_cbg'])
              
      try:
        poi_cbg = str(int(float(poi_cbg)))
      except ValueError:
        regg_count += 1
        continue
              
      # Add the 'poi_cbg' node with 'pois' attribute
      if not G.has_node(poi_cbg):
        G.add_node(poi_cbg, pois=[row['safegraph_place_id']])
      else:
        if 'pois' in G.nodes[poi_cbg].keys():
          G.nodes[poi_cbg]['pois'].append(row['safegraph_place_id'])
        else:
          G.nodes[poi_cbg]['pois'] = [row['safegraph_place_id']]
      
      # Set weight (use 1 if unweighted)
      weight = row['median_dwell'] if weighted and 'median_dwell' in row else 1
      
      # Check if 'visitor_daytime_cbgs' is a string before parsing
      if isinstance(row['visitor_daytime_cbgs'], str):
        try:
          visitor_data = json.loads(row['visitor_daytime_cbgs'])
        except:
          regg_count += 1
          continue
      else:
        regg_count += 1
        continue  # Skip rows where 'visitor_daytime_cbgs' is not a string

      # Ensure visitor_data is a dictionary
      if not isinstance(visitor_data, dict):
        regg_count += 1
        continue

      # Process visitor CBGs
      for visitor_cbg, num_visitors in visitor_data.items():
        try:
          visitor_cbg = str(int(float(visitor_cbg)))  # Convert visitor_cbg to a consistent format
        except:
          regg_count += 1
          continue
        
        if visitor_cbg == poi_cbg:
          continue
        
        # Add or update edge weights
        if G.has_edge(visitor_cbg, poi_cbg):
          G[visitor_cbg][poi_cbg]['weight'] += int(num_visitors * weight)
        else:
          G.add_edge(visitor_cbg, poi_cbg, weight=int(num_visitors * weight))
      
      # Remove nodes without edges
      if G.degree[poi_cbg] == 0:
        G.remove_node(poi_cbg)
    
    # Convert to undirected graph and sum bidirectional weights
    UG = nx.Graph()
    for u, v, data in G.edges(data=True):
      weight = data['weight']
      if UG.has_edge(u, v):
        UG[u][v]['weight'] += weight
      else:
        UG.add_edge(u, v, weight=weight)
    
    print(f"G has {nx.number_of_nodes(UG)} nodes and {nx.number_of_edges(UG)} edges.")
    print("Bad data count:", regg_count)
    
    return UG

cbg_pops = pd.read_csv('safegraph_cbg_population_estimate.csv', index_col='census_block_group')

def cbg_population(cbg):
    try:
        return int(cbg_pops.loc[int(cbg)].B00002e1 * 24)
    except:
        return 1000
      
#get coordinates
gdf['coords'] = gdf['geometry'].apply(lambda x: x.representative_point().coords[:])
gdf['coords'] = [coords[0] for coords in gdf['coords']]
gdf['longitude'] = gdf['coords'].apply(lambda x: x[0])
gdf['latitude'] = gdf['coords'].apply(lambda x: x[1])
print('creating graph')


#To create regular graph
Graph = gen_graph(df)

def find_adjacent_cbgs(gdf, current_cbg):
  """Find directly adjacent CBGs to the current CBG."""
  current_geom = gdf.loc[gdf['GEOID10'] == current_cbg, 'geometry'].values[0]
  neighbors = gdf[gdf.touches(current_geom)]['GEOID10'].tolist()
  return neighbors

def create_cluster(core_cbg, min_pop):
  global gdf
  
  visited = {core_cbg}
  queue = [core_cbg]
  cluster = []
  total_population = 0
  
  while queue and total_population < min_pop:
    current_cbg = queue.pop(0)
    cluster.append(current_cbg)
    total_population += cbg_population(current_cbg)
    
    if total_population >= min_pop:
      break
    
    neighbors = find_adjacent_cbgs(gdf, current_cbg)
    for neighbor in neighbors:
      if neighbor not in visited:
        queue.append(neighbor)
        visited.add(neighbor)
              
  return cluster, total_population, cbg_geocode(core_cbg)
