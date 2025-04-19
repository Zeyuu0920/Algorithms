from datetime import datetime, timedelta
import random
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os
import sys
import time
# 添加路径并导入 us_population_generator
sys.path.append(r'E:\JHU\Research\untitled folder\Algorithms\SP24\refactored')
from US_population_generator import generate_population_data
from preprocess_data import preprocess_csv
from person import Person
from pois import POIs
from enter_poi import enter_poi
from leave_poi import leave_poi
from draw_plot import draw_plot


def main(core_cbg, min_cluster_pop, start_time, simulation_duration):
    # Process CSV Data
    print("Parsing the CSV file...")
    pois_dict = preprocess_csv(file_path)

    # Create POIs with all parameters
    pois = POIs(pois_dict, alpha=alpha, occupancy_weight=occupancy_weight, tendency_decay=tendency_decay)
    print(f"Parsed {len(pois_dict)} POIs. Using alpha={alpha}, occupancy_weight={occupancy_weight}, tendency_decay={tendency_decay}")

    # 直接从 us_population_generator 获取人口数据
    print("Generating population data...")
    papdata = generate_population_data(core_cbg, min_cluster_pop)



    people = {}
    for person_id, person_info in papdata["people"].items():
        person = Person()
        # Set attributes based on papdata.json structure
        person.sex = person_info.get("sex")
        person.age = person_info.get("age")
        person.home = person_info.get("home")
        # Convert person_id to int (if needed) or keep as string based on your Person class implementation
        people[int(person_id)] = person

    start_date = start_time.date()
    print(f"Start date: {start_date}")
    if start_time is None:
        start_time = datetime.datetime.now()
    start_date = start_time.date()

    day_of_week = start_date.weekday()  # 0 for Monday, 6 for Sunday
    day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    current_day_name = day_names[day_of_week]

    # Create DataFrame for result showing
    df = pd.DataFrame(columns=pois.pois)

    '''
    For result tracking:
    '''
    person_1 = list(people.keys())[0]
    person_1_path = []

 

    start_time = datetime.fromisoformat(start_time_str)
    
    # 获取起始日是周几（示例）
    initial_weekday = start_time.weekday()  # 0=周一, 6=周日
    print(f"Startdate {start_time.date()} is {start_time.strftime('%A')}")




    for hour in range(simulation_duration):
        current_time = start_time + timedelta(hours=hour)
        current_weekday = current_time.weekday()
        pass
        
        #for poi_id, poi_data in pois_dict.items():
                #popularity_day = poi_data['popularity_by_day'].get(current_day_name, 0)
                #total_popularity = sum(poi_data['popularity_by_day'].values()) if poi_data['popularity_by_day'] else 1
                #if total_popularity > 0:
                     #entry_probability = popularity_day / total_popularity
                #else:
                     #entry_probability = 0
                #poi_data['entry_probability'] = entry_probability
        print(f"Simulating hour {hour + 1}/{simulation_duration} at {current_time}...")
        leave_poi(people, current_time, pois)
        # Use the actual number of persons from papdata.json
        enter_poi(people, pois, current_time, len(people))

        #for poi_data in pois_dict.values():
            #if 'entry_probability' in poi_data:
                #del poi_data['entry_probability']



        '''
        For result logging:
        '''
        capacities = pois.get_capacities_by_time(current_time)
        occupancies = pois.occupancies


        # Write capacity vs occupancy data to file
        with open('output/capacity_occupancy.csv', 'a', encoding='utf-8') as f:
            f.write(f"\nHour {hour}:\n")
            for poi_id in pois.pois:
                poi_name = pois_dict[poi_id]['location_name']
                cap = capacities[poi_id]
                occ = occupancies[poi_id]
                diff = cap - occ
                f.write(f"{poi_name},{cap:.2f},{occ},{diff:.2f}\n")

        if people[person_1].curr_poi != "":
            person_1_path.append(pois_dict[people[person_1].curr_poi]['location_name'])
        else:
            person_1_path.append("at home")
        df.loc[hour] = pois.occupancies

        updated_homes = {}
    updated_places = {}
    for person in people.values():
        if person.at_home():
            home_id = person.household.id
            if home_id not in updated_homes:
                updated_homes[home_id] = []
            updated_homes[home_id].append(person.id)
        else:
            poi_id = person.curr_poi
            if poi_id:  # 确保 curr_poi 有效
                if poi_id not in updated_places:
                    updated_places[poi_id] = []
                updated_places[poi_id].append(person.id)

    # 构建输出字典
    output = {
        simulation_duration: {
            "homes": updated_homes,
            "places": updated_places
        }
    }

    # 可选：打印或保存输出
    import json
    print("Simulation output:", json.dumps(output, indent=2, ensure_ascii=False))
    
    return output
'''''
    # Print the path of person 1
    print("Person 1 path:", person_1_path)
    print("Person 1 age is", people[person_1].age, 
        "sex:", 'male' if people[person_1].sex == 0 else 'female',"home:", people[person_1].home)

    with open('output/pattern.json', 'w', encoding='utf-8') as f:
        json.dump(papdata, f, indent=2, ensure_ascii=False)
    print("Full papdata saved to output/papdata.json")


    # Save the DataFrame to a CSV file
    output_file = "output/simulation_results.csv"
    df.to_csv(output_file, index=True)
    location_names = [pois_dict[list(pois_dict.keys())[i]]['location_name'] for i in range(len(df.columns))]
    df.columns = location_names

    # Save df and location names to files
    df.to_csv('output/occupancy_df.csv', index=True)
    with open('output/location_names.txt', 'w', encoding='utf-8') as f:
        for location in location_names:
            f.write(f"{location}\n")

    #draw_plot(df, location_names)

    # Draw the plot
'''''
def draw_plot(df, location_names):
    # Create output directory
    os.makedirs('output', exist_ok=True)
    
    # Create figure
    plt.figure(figsize=(15, 8))
    
    # Sort locations by final occupancy and get top 20
    final_occupancies = df.iloc[-1]
    sorted_locations = final_occupancies.sort_values(ascending=False).index[:20]
    
    # Create color palette
    colors = plt.cm.tab20(np.linspace(0, 1, 20))
    
    # Plot each location
    for idx, location in enumerate(sorted_locations):
        try:
            # Ensure we're working with a Series
            values = df[location] if isinstance(df[location], pd.Series) else df[location].iloc[:, 0]
            plt.plot(df.index, values, label=location, color=colors[idx])
        except Exception as e:
            print(f"Error plotting {location}: {e}")
            continue
    
    plt.xlabel('Time (hours)')
    plt.ylabel('Number of People')
    plt.title('Top 20 POI Occupancy Over Time')
    plt.grid(True)
    
    # Add legend
    plt.legend(loc='center left', 
              bbox_to_anchor=(1, 0.5),
              title='Top 20 Locations')
    
    # Save plot
    plt.savefig('output/occupancy_plot.png', 
                bbox_inches='tight',
                dpi=300,
                pad_inches=0.5)
    plt.close()
'''''

town_name='hagerstown'
start_time_str='2025-01-01T00:00:00'

alpha=0.16557695315916893
occupancy_weight=1.5711109677337263
tendency_decay=0.3460627088857086
start_time = datetime.fromisoformat(start_time_str)  
file_path = r'E:\JHU\Research\untitled folder\Delineo-movement-simulation-pattern-master\input\hagerstown.csv'
# ...existing code...
if __name__ == "__main__":
    import time
    start_time_execution = time.time()
    start_time_str='2025-01-01T00:00:00'
    start_time = datetime.fromisoformat(start_time_str)  
        
    main(core_cbg='240430006012', min_cluster_pop=5000,start_time=start_time,simulation_duration=24)
         
    end_time_execution = time.time()
    print(f"Total execution time: {end_time_execution - start_time_execution:.2f} seconds")
