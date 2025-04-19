import csv
import json

def parse_json_field(field):
    if not field:
        return {}
    try:
        return json.loads(field)
    except json.JSONDecodeError:
        return {}

def compute_dwell_time_cdf(bucketed_dwell_times):
    """
    Compute the cumulative distribution function (CDF) of dwell times,
    grouping 0-60 minutes together and considering 120-240 minutes as covering 120-180 and 180-240.
    """
    # Map dwell time buckets to representative times in hours
    dwell_time_buckets = {
        '<60': 1,          # Group 0-60 minutes together as 1 hour
        '61-120': 1.5,     # Average of 61-120 minutes = 1.5 hours
        '121-240': 3,      # Average of 120-180 and 180-240 minutes = 3 hours
        '>240': 5          # Assume 5 hours for >240 minutes
    }
    
    # Combine counts for 0-60 minutes
    count_under_60 = (
        bucketed_dwell_times.get('<5', 0) +
        bucketed_dwell_times.get('5-10', 0) +
        bucketed_dwell_times.get('11-20', 0) +
        bucketed_dwell_times.get('21-60', 0)
    )
    
    # Combine counts for 121-240 minutes
    count_121_240 = bucketed_dwell_times.get('121-240', 0)
    # If there were separate counts for 120-180 and 180-240, sum them up
    # Since in your data it's '121-240', we use that directly

    # Build the adjusted bucketed dwell times
    adjusted_bucketed_dwell_times = {
        '<60': count_under_60,
        '61-120': bucketed_dwell_times.get('61-120', 0),
        '121-240': count_121_240,
        '>240': bucketed_dwell_times.get('>240', 0)
    }
    
    # Total count of visits
    total_visits = sum(adjusted_bucketed_dwell_times.values())
    
    # Compute probabilities
    dwell_times = []
    probabilities = []
    for bucket in ['<60', '61-120', '121-240', '>240']:
        count = adjusted_bucketed_dwell_times.get(bucket, 0)
        probability = count / total_visits if total_visits > 0 else 0
        dwell_time = dwell_time_buckets.get(bucket, 5)  # Default to 5 hours if not specified
        dwell_times.append(dwell_time)
        probabilities.append(probability)
    
    # Compute CDF
    cdf = []
    cumulative_prob = 0
    for prob in probabilities:
        cumulative_prob += prob
        cdf.append(cumulative_prob)
    
    return dwell_times, cdf

def preprocess_csv(file_path):
    pois_dict = {}
    
    with open(file_path, mode='r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            safegraph_place_id = row['safegraph_place_id']

            if not safegraph_place_id:
                continue  
            '''''
            # 解析 popularity_by_day
            popularity_by_day = parse_json_field(row.get('popularity_by_day', '{}'))

            '''''

            # 其他现有逻辑保持不变
            sum_popularity = sum(parse_json_field(row['popularity_by_hour'])) 
            probability_by_hour = [p / sum_popularity for p in parse_json_field(row['popularity_by_hour'])] if sum_popularity > 0 else []

            bucketed_dwell_times = parse_json_field(row['bucketed_dwell_times'])
            dwell_times, dwell_time_cdf = compute_dwell_time_cdf(bucketed_dwell_times)

            related_same_month_brand = parse_json_field(row['related_same_month_brand'])
            sum_tendency = sum(related_same_month_brand.values())
            after_tendency = {poi_id : related_same_month_brand.get(pois_dict.get(poi_id, {}).get('location_name', ''), 0) / sum_tendency  if sum_tendency > 0 else 0 for poi_id in pois_dict.keys()}

            # 更新 pois_dict，添加 popularity_by_day
            pois_dict[safegraph_place_id] = {
                'location_name': row['location_name'],
                'raw_visit_counts': int(row['raw_visit_counts']),
                'raw_visitor_counts': int(row['raw_visitor_counts']),
                'visits_by_day': parse_json_field(row['visits_by_day']),
                'probability_by_hour': probability_by_hour,
                'dwell_times': dwell_times,
                'dwell_time_cdf': dwell_time_cdf,
                'related_same_day_brand': parse_json_field(row['related_same_day_brand']),
                'after_tendency': after_tendency,
                #'popularity_by_day': popularity_by_day
            } 

    return pois_dict


if __name__ == "__main__":
    pois_dict = preprocess_csv('Delineo-movement-simulation-pattern-master/input/hagerstown.csv')
    print(pois_dict)

# Example usage