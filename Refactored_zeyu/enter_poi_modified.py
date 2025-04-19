import random
import datetime

def enter_poi(people, pois, current_time, num_people):
    """
    模拟人员进入 POI。
    """
    for person in people:
        if person.need_new_poi(current_time):
            poi_id = random.choice(list(pois.keys()))
            person.location = type('POI', (), {'id': poi_id})
            person.last_poi_time = current_time
            person.availability = True
            print(f"Person {person.id} entered POI {poi_id} at {current_time}")