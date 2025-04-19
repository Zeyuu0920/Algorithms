import csv
import math
import numpy as np
from scipy import stats
#test

def calculate_metrics(file_path):
    capacities = []
    occupancies = []
    differences = []
    hourly_data = {}
    
    with open(file_path, 'r') as file:
        reader = csv.reader(file)
        current_hour = None
        
        for row in reader:
            if len(row) == 0:
                continue
                
            if row[0].startswith('\nHour'):
                hour_str = row[0].strip().split()[1].rstrip(':')
                current_hour = int(hour_str)
                hourly_data[current_hour] = {'capacities': [], 'occupancies': []}
                continue
                
            if len(row) >= 4:  # location_name, capacity, occupancy, difference
                try:
                    capacity = float(row[1])
                    occupancy = float(row[2])
                    
                    # Round up and down both values and compare
                    ceil_capacity = math.ceil(capacity)
                    ceil_occupancy = math.ceil(occupancy)
                    floor_capacity = math.floor(capacity)
                    floor_occupancy = math.floor(occupancy)
                    
                    if ceil_occupancy == ceil_capacity or floor_occupancy == floor_capacity:
                        difference = 0  # Exact match after either rounding method
                    else:
                        difference = occupancy - capacity  # Use original values for difference
                    
                    if capacity > 0:  # Only count locations with non-zero capacity
                        capacities.append(capacity)
                        occupancies.append(occupancy)
                        differences.append(difference)
                        
                        if current_hour is not None:
                            hourly_data[current_hour]['capacities'].append(capacity)
                            hourly_data[current_hour]['occupancies'].append(occupancy)
                        
                except (ValueError, IndexError):
                    continue
    
    # Basic error metrics
    n = len(capacities)
    if n == 0:
        return {'error': 'No valid data points found'}
    
    mse = sum(d ** 2 for d in differences) / n
    rmse = math.sqrt(mse)
    mae = sum(abs(d) for d in differences) / n
    
    # Calculate correlation between capacity and occupancy
    correlation, _ = stats.pearsonr(capacities, occupancies)
    
    # Calculate peak timing error
    peak_error = calculate_peak_timing_error(hourly_data)
    
    # Calculate accuracy (as percentage)
    average_error_rate = mae / (sum(capacities) / n) if sum(capacities) > 0 else 1.0
    accuracy = max(0.0, min(1.0, 1.0 - average_error_rate)) * 100
    
    return {
        'total_capacity': sum(capacities),
        'total_occupancy': sum(occupancies),
        'total_difference': sum(differences),
        'number_of_locations': n,
        'mean_squared_error': mse,
        'root_mean_squared_error': rmse,
        'mean_absolute_error': mae,
        'correlation': correlation,
        'peak_error': peak_error,
        'accuracy': accuracy
    }

def calculate_peak_timing_error(hourly_data):
    """Calculate the average difference in peak timing between capacity and occupancy"""
    peak_timing_errors = []
    
    for hour, data in hourly_data.items():
        if not data['capacities'] or not data['occupancies']:
            continue
            
        capacity_sum = sum(data['capacities'])
        occupancy_sum = sum(data['occupancies'])
        
        if capacity_sum > 0 and occupancy_sum > 0:
            peak_timing_errors.append(abs(
                capacity_sum / max(sum(d['capacities']) for d in hourly_data.values()) -
                occupancy_sum / max(sum(d['occupancies']) for d in hourly_data.values())
            ))
    
    return sum(peak_timing_errors) / len(peak_timing_errors) if peak_timing_errors else 1.0

# Usage
metrics = calculate_metrics('output/capacity_occupancy.csv')

print(f"Analysis Results:")
print(f"Number of locations with capacity: {metrics['number_of_locations']}")
print(f"Total Capacity: {metrics['total_capacity']:.2f}")
print(f"Total Occupancy: {metrics['total_occupancy']:.2f}")
print(f"Total Difference: {metrics['total_difference']:.2f}")
print(f"\nError Metrics:")
print(f"Mean Squared Error: {metrics['mean_squared_error']:.4f}")
print(f"Root Mean Squared Error: {metrics['root_mean_squared_error']:.4f}")
print(f"Mean Absolute Error: {metrics['mean_absolute_error']:.4f}")
print(f"Accuracy: {metrics['accuracy']:.2f}%")  # Add accuracy to output