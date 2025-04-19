from person import Person
from pois import POIs
import random

def leave_poi(people, current_time, pois, place_id_to_safegraph):
    """
    Optimized function to simulate leaving a certain POI.
    
    Args:
        people: Dictionary of Person objects.
        current_time: Current time in the simulation.
        pois: POIs object containing POI data.
        place_id_to_safegraph: Dictionary mapping papdata["places"] IDs to SafeGraph IDs.
    """
    for person_id, person in people.items():
        if not person.is_poi:
            continue  

        # 映射 person.curr_poi 回 SafeGraph ID
        poi_id = place_id_to_safegraph.get(person.curr_poi, person.curr_poi)
        hour_stayed = person.hour_stayed

        # Get dwell time CDF for the current POI
        dwell_times, dwell_time_cdf = pois.get_dwell_time_cdf(poi_id)

        # Find the probability of leaving based on the dwell time
        index = next((i for i, dt in enumerate(dwell_times) if dt >= hour_stayed), len(dwell_time_cdf) - 1)
        leave_prob = dwell_time_cdf[index]

        # Adjust leave probability based on occupancy
        expected_capacity = pois.capacities[current_time.day].get(poi_id, 1)
        current_occupancy = pois.occupancies.get(poi_id, 0)
        if expected_capacity > 0:
            occupancy_ratio = current_occupancy / expected_capacity
        else:
            occupancy_ratio = 0

        # Modify leave probability with occupancy
        if occupancy_ratio > 1:  # Over-occupied POI
            leave_prob *= occupancy_ratio
        else:  # Under-occupied POI
            leave_prob *= 0.5

        # Clamp leave probability between 0 and 1
        leave_prob = min(max(leave_prob, 0), 1)

        # Decide if the person leaves
        if random.random() < leave_prob:
            person.leave()
            pois.occupancies[poi_id] = max(0, current_occupancy - 1)  # Decrement occupancy
        else:
            person.stay()