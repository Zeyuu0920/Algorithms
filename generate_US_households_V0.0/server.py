from flask import Flask, request, jsonify
import json
import pandas as pd
import networkx as nx
import pickle
import geopandas as gpd
from geopy.geocoders import Nominatim
from math import sin, cos, atan2, pi, sqrt

app = Flask(__name__)

with open("cz_graph.pkl", "rb") as file:
    G = pickle.load(file)

# i think this loads CBG geographic data
gdf1 = gpd.read_file('tl_2010_24_bg10/tl_2010_24_bg10.shp')
gdf2 = gpd.read_file('tl_2010_42_bg10/tl_2010_42_bg10.shp')
gdf3 = gpd.read_file('tl_2010_40_bg10/tl_2010_40_bg10.shp')
gdf = gpd.GeoDataFrame(pd.concat([gdf1, gdf2, gdf3], ignore_index=True))

geolocator = Nominatim(user_agent="cbg_finder")


def find_core_cbg(city_name):
    """Finds the CBG that contains a given city location."""
    location = geolocator.geocode(city_name)
    if location is None:
        return None

    point = gpd.GeoSeries(gpd.points_from_xy(
        [location.longitude], [location.latitude]), crs="EPSG:4326")
    cbg_row = gdf[gdf.contains(point.geometry[0])]

    return cbg_row.iloc[0]['GEOID10'] if not cbg_row.empty else None


def find_adjacent_cbgs(current_cbg):
    """Find directly adjacent CBGs using geographic boundaries."""
    row = gdf[gdf['GEOID10'] == current_cbg]
    return gdf[gdf.touches(row.geometry.values[0])]['GEOID10'].tolist() if not row.empty else []


def generate_cz(cbg):
    """Generate the Convenience Zone (CZ) for a given CBG."""
    if cbg not in G.nodes:
        return []

    cz_cbg_list = list(G.neighbors(cbg))

    if len(cz_cbg_list) < 5:
        cz_cbg_list.extend(find_adjacent_cbgs(cbg))

    return list(set(cz_cbg_list))


@app.route('/')
def home():
    return jsonify({"message": "Welcome to the Convenience Zone Generator API!"})


@app.route('/generate_cz', methods=['POST'])
def generate_cz_api():
    """API endpoint to get a list of CBGs forming the Convenience Zone."""
    data = request.get_json()

    if not data:
        return jsonify({"error": "Invalid JSON request"}), 400

    location = data.get("location")
    cbg = data.get("cbg")

    if not location and not cbg:
        return jsonify({"error": "Provide either 'location' (city name) or 'cbg'"}), 400

    if location:
        cbg = find_core_cbg(location)
        if not cbg:
            return jsonify({"error": "Unable to find CBG for the given location"}), 400

    # get convenience zone?
    cz_list = generate_cz(cbg)

    return jsonify({"cbg_list": cz_list})


if __name__ == '__main__':
    app.run(debug=True)
