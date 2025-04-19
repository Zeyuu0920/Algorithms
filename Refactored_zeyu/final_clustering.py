

import geopandas as gpd
import numpy as np
import pandas as pd
import networkx as nx
import json
import pickle
#from uszipcode import SearchEngine
from math import sin, cos, atan2, pi, sqrt
import yaml

# Global variables
zip_codes = []
# Load zip codes

zip_codes_md = [20601, 20602, 20603, 20607, 20611]  
zip_codes_pa = [15001, 15003, 15004, 15005, 15006]  
zip_codes = zip_codes_md + zip_codes_pa

# Load SafeGraph data
def load_safegraph_data():
    filename = r'E:\JHU\Research\untitled folder\Algorithms\SP24\refactored\hagerstown.csv'  # 更新为实际路径
    try:
        df = pd.read_csv(filename)
    except FileNotFoundError:
        datalist = []
        with pd.read_csv('patterns.csv', chunksize=10000) as reader:
            for chunk in reader:
                datalist.append(chunk[chunk['postal_code'].isin(zip_codes)])
        df = pd.concat(datalist, axis=0)
        del datalist
        try:
            df['poi_cbg'] = df['poi_cbg'].astype('int64')
        except:
            pass
        df.to_csv(filename)
    
    # Load POI data
    poi_filename = r'E:\JHU\Research\untitled folder\Algorithms\SP24\refactored\hagerstown.pois.csv'  # 更新为实际路径
    try:
        poif = pd.read_csv(poi_filename)
    except FileNotFoundError:
        datalist = []
        with pd.read_csv('2021_05_05_03_core_poi.csv', chunksize=10000) as reader:
            for chunk in reader:
                datalist.append(chunk[chunk['postal_code'].isin(zip_codes)])
        poif = pd.concat(datalist, axis=0)
        del datalist
        poif.to_csv(poi_filename)
    
    return df, poif

# Helper functions
def cbg_geocode(cbg, df, poif):
    lat = []
    long = []
    for _, poi in df.loc[df['poi_cbg'] == int(cbg)].iterrows():
        poi_info = poif.loc[poif['safegraph_place_id'] == poi['safegraph_place_id']]
        if not poi_info.empty:
            lat.append(poi_info.iloc[0]['latitude'])
            long.append(poi_info.iloc[0]['longitude'])
    return pd.Series(data={
        'label': str(cbg),
        'latitude': np.mean(lat) if lat else None,
        'longitude': np.mean(long) if long else None
    })

def distance(lat1, long1, lat2, long2):
    lat1 = lat1 * pi / 180
    long1 = long1 * pi / 180
    lat2 = lat2 * pi / 180
    long2 = long2 * pi / 180
    Radius = 6371
    haversine = sin((lat2 - lat1) / 2) ** 2 + cos(lat1) * cos(lat2) * sin((long2 - long1) / 2) ** 2
    c = 2 * atan2(sqrt(haversine), sqrt(1 - haversine))
    return Radius * c

def gen_graph(df):
    G = nx.Graph()
    regg_count = 0
    for _, row in df.iterrows():
        poi_cbg = str(row['poi_cbg'])
        try:
            int_poi = int(float(poi_cbg))
            poi_cbg = str(int_poi)
        except:
            regg_count += 1
            continue
        G.add_node(poi_cbg, pois=[])
        G.nodes[poi_cbg]['pois'].append(row['safegraph_place_id'])
        weight = row['median_dwell'] if True else 1
        for visitor_cbg, num_visitors in json.loads(row['visitor_daytime_cbgs']).items():
            if visitor_cbg == poi_cbg:
                continue
            if G.has_edge(visitor_cbg, poi_cbg):
                try:
                    G[visitor_cbg][poi_cbg]['weight'] += int(num_visitors * weight)
                except ZeroDivisionError:
                    continue
            else:
                try:
                    G.add_weighted_edges_from([(visitor_cbg, poi_cbg, int(num_visitors * weight))])
                except ZeroDivisionError:
                    continue
        if G.degree[poi_cbg] == 0:
            G.remove_node(poi_cbg)
    UG = G.to_undirected()
    for node in G:
        for node2 in nx.neighbors(G, node):
            if node in nx.neighbors(G, node2):
                UG.edges[node, node2]['weight'] = G.edges[node, node2]['weight'] + G.edges[node2, node]['weight']
    print(f'G has {nx.number_of_nodes(UG)} nodes and {nx.number_of_edges(UG)} edges.')
    print("bad data ", regg_count)
    return UG

def cbg_population(cbg, cbg_pops):
    try:
        return int(cbg_pops.loc[int(cbg)].B00002e1)
    except (ValueError, TypeError, KeyError):
        return 0

def greedy_weight(G, u0, min_pop):
    cluster = [u0]
    population = cbg_population(u0, cbg_pops)
    while population < min_pop:
        all_adj_cbgs = []
        for i in cluster:
            adj_cbgs = list(G.adj[i])
            for j in adj_cbgs:
                if j not in all_adj_cbgs and j not in cluster:
                    all_adj_cbgs.append(j)
        max_movement = 0
        cbg_to_add = None
        for i in all_adj_cbgs:
            current_movement = 0
            for j in cluster:
                try:
                    current_movement += G.adj[i][j]['weight']
                except:
                    pass
            if current_movement > max_movement:
                max_movement = current_movement
                cbg_to_add = i
        if cbg_to_add:
            cluster.append(cbg_to_add)
            population += cbg_population(cbg_to_add, cbg_pops)
    return cluster, population

# Main function to get cbg_info
def get_cbg_info(core_cbg, min_cluster_pop):
    # Load data
    df, poif = load_safegraph_data()
    
    # Load shapefiles
    gdf1 = gpd.read_file(r'E:\JHU\Research\untitled folder\Algorithms\tl_2010_24_bg10')
    gdf2 = gpd.read_file(r'E:\JHU\Research\untitled folder\Algorithms\tl_2010_42_bg10')
    gdf = gpd.GeoDataFrame(pd.concat([gdf1, gdf2], ignore_index=True))
    gdf['coords'] = gdf['geometry'].apply(lambda x: x.representative_point().coords[:])
    gdf['coords'] = [coords[0] for coords in gdf['coords']]
    gdf['longitude'] = gdf['coords'].apply(lambda x: x[0])
    gdf['latitude'] = gdf['coords'].apply(lambda x: x[1])

    # Load population data
    global cbg_pops
    cbg_pops = pd.read_csv(r'E:\JHU\Research\untitled folder\Algorithms\safegraph_cbg_population_estimate.csv', index_col='census_block_group')

    # Generate graph
    G = gen_graph(df)

    # Run clustering algorithm
    algorithm_result = greedy_weight(G, core_cbg, min_cluster_pop)

    # Generate cbg_info
    cbg_info_list = []
    for cbg in algorithm_result[0]:
        cbg_str = str(cbg)
        pop_est = cbg_population(cbg, cbg_pops)
        movement_in_S = 0
        movement_out_S = 0
        for neighbor in G.adj[cbg]:
            if neighbor in algorithm_result[0]:
                movement_in_S += G.adj[cbg][neighbor]['weight'] / 2
            else:
                movement_out_S += G.adj[cbg][neighbor]['weight']
        total_movement = movement_in_S + movement_out_S
        ratio = movement_in_S / total_movement if total_movement > 0 else None
        cbg_info_list.append({
            "GEOID10": cbg_str,
            "movement_in": movement_in_S,
            "movement_out": movement_out_S,
            "ratio": ratio,
            "estimated_population": pop_est
        })
    
    return cbg_info_list

#if __name__ == "__main__":
    location_name = "Hagerstown"
    core_cbg = "240010001001"
    min_cluster_pop = 5000
    cbg_info = get_cbg_info()
    print("CBG Info generated successfully:", cbg_info)
    print(cbg_info)