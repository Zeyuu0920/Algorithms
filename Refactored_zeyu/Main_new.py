#Main_new.py
from datetime import datetime, timedelta
import random
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os
import sys
import time
from datetime import datetime, timedelta
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
    # 参数配置
    file_path = r'E:\JHU\Research\untitled folder\Delineo-movement-simulation-pattern-master\input\hagerstown.csv'
    alpha = 0.16557695315916893
    occupancy_weight = 1.5711109677337263
    tendency_decay = 0.3460627088857086

    # Process CSV Data
    print("Parsing the CSV file...")
    pois_dict = preprocess_csv(file_path)
    pois = POIs(pois_dict, alpha=alpha, occupancy_weight=occupancy_weight, tendency_decay=tendency_decay)
    print(f"Parsed {len(pois_dict)} POIs. Using alpha={alpha}, occupancy_weight={occupancy_weight}, tendency_decay={tendency_decay}")

    # 生成人口数据
    print("Generating population data...")
    papdata = generate_population_data(core_cbg, min_cluster_pop)

    safegraph_to_place_id = {}
    place_id_to_safegraph = {}
    place_ids = sorted(papdata["places"].keys(), key=int)
    safegraph_ids = sorted(pois_dict.keys())
    if len(place_ids) != len(safegraph_ids):
        print("Warning: Number of places in papdata does not match number of POIs in pois_dict")
    for place_id, sg_id in zip(place_ids, safegraph_ids):
        safegraph_to_place_id[sg_id] = place_id
        place_id_to_safegraph[place_id] = sg_id

    # 创建 Person 对象
    people = {}
    for person_id, person_info in papdata["people"].items():
        person = Person()
        person.id = int(person_id)  # 设置 ID
        person.sex = person_info.get("sex")
        person.age = person_info.get("age")
        person.home = person_info.get("home")
        people[int(person_id)] = person

    # 时间初始化
    start_date = start_time.date()
    print(f"Start date: {start_date}")
    if start_time is None:
        start_time = datetime.datetime.now()
    start_date = start_time.date()

    day_of_week = start_date.weekday()
    day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    current_day_name = day_names[day_of_week]
    print(f"Start date {start_date} is {current_day_name}")

    # 跟踪示例人员
    person_1 = list(people.keys())[0]
    person_1_path = []

    output = {}

    # 模拟循环
    for hour in range(simulation_duration):
        current_time = start_time + timedelta(hours=hour)
        current_weekday = current_time.weekday()
        print(f"Simulating hour {hour + 1}/{simulation_duration} at {current_time}...")
        leave_poi(people, current_time, pois, place_id_to_safegraph)
        enter_poi(people, pois, current_time, len(people),safegraph_to_place_id, place_id_to_safegraph)

        # 跟踪 person_1
        if people[person_1].curr_poi != "":
            # 将 curr_poi 转换回 SafeGraph ID 以访问 pois_dict
            safegraph_poi_id = place_id_to_safegraph.get(people[person_1].curr_poi, people[person_1].curr_poi)
            person_1_path.append(pois_dict[safegraph_poi_id]['location_name'])
        else:
            person_1_path.append("at home")
            
        # 记录当前时间点的状态（以分钟为键）
        current_minutes = (hour + 1) * 60  # hour=0 → 60 分钟, hour=1 → 120 分钟, ...
        updated_homes = {}
        updated_places = {}
        for person in people.values():
            if person.at_home():
                home_id = str(person.home)
                if home_id not in updated_homes:
                    updated_homes[home_id] = []
                updated_homes[home_id].append(str(person.id))
            else:
                poi_id = person.curr_poi
                if poi_id:
                    poi_id = str(poi_id)
                    if poi_id not in updated_places:
                        updated_places[poi_id] = []
                    updated_places[poi_id].append(str(person.id))
        output[str(current_minutes)] = {
            "homes": updated_homes,
            "places": updated_places
        }

    # 打印 person_1 路径
    print("Person 1 path:", person_1_path)

    # 收集更新后的 homes 和 places
    updated_homes = {}
    updated_places = {}
    for person in people.values():
        if person.at_home():  # 使用 is_poi 判断是否在家
            home_id = str(person.home)  # 确保为字符串
            if home_id not in updated_homes:
                updated_homes[home_id] = []
            updated_homes[home_id].append(str(person.id))
        else:
            poi_id = person.curr_poi
            if poi_id:  # 确保 curr_poi 有效
                mapped_poi_id = safegraph_to_place_id.get(poi_id, poi_id)
                if mapped_poi_id not in updated_places:
                    updated_places[mapped_poi_id] = []
                updated_places[mapped_poi_id].append(str(person.id))

    output["0"] = {
        "homes": updated_homes,
        "places": updated_places
    }

    # 打印输出
    #print("Simulation output:", json.dumps(output, indent=2, ensure_ascii=False))

    return output, papdata

if __name__ == "__main__":
    import time
    start_time_execution = time.time()
    start_time_str = '2025-01-01T00:00:00'
    start_time = datetime.fromisoformat(start_time_str)
    
    output = main(core_cbg='240430006012', min_cluster_pop=5000, start_time=start_time, simulation_duration=24)
    #print("Final output:", json.dumps(output, indent=2, ensure_ascii=False))


    output_dir = 'output'
    os.makedirs(output_dir, exist_ok=True)  # 确保 output 目录存在
    output_file = os.path.join(output_dir, 'final_output.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"Output saved to {output_file}")
    
    end_time_execution = time.time()
    print(f"Total execution time: {end_time_execution - start_time_execution:.2f} seconds")