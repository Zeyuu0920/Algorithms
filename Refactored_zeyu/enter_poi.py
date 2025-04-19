import random

def enter_poi(people, pois, current_time, hagerstown_pop, safegraph_to_place_id, place_id_to_safegraph):
    """
    Modified enter_poi to map SafeGraph IDs to papdata["places"] IDs.
    
    Args:
        people: Dictionary of Person objects.
        pois: POIs object containing POI data.
        current_time: Current time in the simulation.
        hagerstown_pop: Population size of Hagerstown.
        safegraph_to_place_id: Dictionary mapping SafeGraph IDs to papdata["places"] IDs.
        place_id_to_safegraph: Dictionary mapping papdata["places"] IDs to SafeGraph IDs.
    """
    move_probability, distribution = pois.generate_distribution(current_time, hagerstown_pop)
    move_probability_with_tendency, distributions_with_tendency = pois.generate_distributions_with_tendency(current_time, hagerstown_pop)
    for person_id, person in people.items():
        if person.curr_poi == "":
            next_poi_id = pois.get_next_poi(move_probability, distribution)
        else:
            # 将 person.curr_poi 转换回 SafeGraph ID
            safegraph_poi_id = place_id_to_safegraph.get(person.curr_poi, person.curr_poi)
            curr_poi_index = pois.poi_id_to_index[safegraph_poi_id]  # 使用 SafeGraph ID 查找索引
            next_poi_id = pois.get_next_poi(move_probability_with_tendency[curr_poi_index], distributions_with_tendency[curr_poi_index])
        if next_poi_id is not None:
            # 映射 SafeGraph ID 到 papdata["places"] ID
            mapped_poi_id = safegraph_to_place_id.get(next_poi_id, next_poi_id)
            pois.enter(next_poi_id)  # pois.enter 仍使用 SafeGraph ID
            person.visit(mapped_poi_id)  # person.visit 使用映射后的 ID