import numpy as np

class POIs:
    def __init__(self, pois_dict, alpha=0.1, occupancy_weight=1.0, tendency_decay=0.5):
        self.alpha = alpha
        self.occupancy_weight = occupancy_weight
        self.tendency_decay = tendency_decay
        # pois = [poi_id, ...]
        self.pois = list(pois_dict.keys())
        # pois_id_to_index = {poi_id: index}
        self.poi_id_to_index = {poi_id: index for index, poi_id in enumerate(self.pois)}
        # raw_visit_counts = {poi_id: raw_visit_counts}
        self.raw_visit_counts = {poi_id: pois_dict[poi_id]['raw_visit_counts'] for poi_id in pois_dict}
        # raw_visitor_counts = {poi_id: raw_visitor_counts}
        self.raw_visitor_counts = {poi_id: pois_dict[poi_id]['raw_visitor_counts'] for poi_id in pois_dict}
        # capacities = [{poi_id: capacity} for 30 days]
        self.capacities = [{poi_id: pois_dict[poi_id]['visits_by_day'][i] for poi_id in pois_dict} for i in range(30)]
        # probabilities = [{poi_id: probability} for 24 hours]
        self.probabilities = [{poi_id: pois_dict[poi_id]['probability_by_hour'][i] for poi_id in pois_dict} for i in range(24)]
        # {prev_poi_id: {after_poi_id: tendency}}
        self.tendency_probabilities = {poi_id: pois_dict[poi_id]['after_tendency'] for poi_id in pois_dict}
        # {poi_id: occupancy}
        self.occupancies = {poi_id: 0 for poi_id in pois_dict}
        # Dwell times and CDFs
        self.dwell_times = {poi_id: pois_dict[poi_id]['dwell_times'] for poi_id in pois_dict}
        self.dwell_time_cdfs = {poi_id: pois_dict[poi_id]['dwell_time_cdf'] for poi_id in pois_dict}

    def get_capacities_by_day(self, current_time):
        return self.capacities[current_time.day]

    def get_probabilities_by_time(self, current_time):
        return self.probabilities[current_time.hour]
    
    def get_capacities_by_time(self, current_time):
        return {poi_id: self.capacities[current_time.day][poi_id] * self.probabilities[current_time.hour][poi_id] for poi_id in self.capacities[current_time.day]}
    
    def get_after_tendencies(self, prev_poi_id):
        return {after_poi_id: self.tendency_probabilities[prev_poi_id].get(after_poi_id, 0) for after_poi_id in self.pois}
    
    def get_dwell_time_cdf(self, poi_id):
        return self.dwell_times[poi_id], self.dwell_time_cdfs[poi_id]
    
    def capacity_occupancy_diff(self, current_time):
        C = np.array(list(self.get_capacities_by_time(current_time).values()))
        O = np.array(list(self.occupancies.values()))
        return np.maximum(C - O, 0)
    
    def capacity_occupancy_diff_with_tendency(self, current_time, population):
        C = np.array(list(self.get_capacities_by_time(current_time).values()))
        O = np.array(list(self.occupancies.values()))
        A = np.array([list(self.get_after_tendencies(poi_id).values()) for poi_id in self.pois])
        
        # Apply occupancy weight to capacity-occupancy difference
        capacity_term = np.maximum(C - O, 0) * self.occupancy_weight
        
        # Apply tendency decay based on time spent
        tendency_term = A * self.alpha * (1 - self.tendency_decay)
        
        return (tendency_term + capacity_term[:, np.newaxis]) / population
    
    def generate_distribution(self, current_time, population):
        distribution = self.capacity_occupancy_diff(current_time)
        move_probability = sum(distribution) / population
        # normalize distribution
        return move_probability, distribution / np.sum(distribution) if np.sum(distribution) > 0 else np.zeros_like(distribution)
    
    def generate_distributions_with_tendency(self, current_time, population):
        distributions = self.capacity_occupancy_diff_with_tendency(current_time, population)
        move_probabilities = [sum(distribution) / population for distribution in distributions]
        # normalize distributions
        return move_probabilities, [distribution / np.sum(distribution) if np.sum(distribution) > 0 else np.zeros_like(distribution) for distribution in distributions]

    def get_next_poi(self, move_probability, distribution):
        if np.random.random() < move_probability:
            return np.random.choice(self.pois, p=distribution)
        else:
            return None
    
    def leave(self, poi_id):
        self.occupancies[poi_id] -= 1

    def enter(self, poi_id):
        self.occupancies[poi_id] += 1