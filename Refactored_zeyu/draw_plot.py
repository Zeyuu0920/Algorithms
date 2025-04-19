import matplotlib.pyplot as plt
import pandas as pd

def draw_plot(df, location_names):
    # Create plot for the graph
    plt.figure(figsize=(20, 10))
    
    # Create the plot and store the line objects
    lines = []
    for location in location_names:
        line, = plt.plot(df.index, df[location], label=location)
        lines.append(line)
    
    plt.xlabel('Hour')
    plt.ylabel('Occupancy')
    plt.title('POI Occupancy Over Time')
    
    # Save the graph without the legend
    plt.savefig('output/occupancy_graph.png', bbox_inches='tight', dpi=300)
    plt.close()
    
    # Create a separate plot for the legend
    plt.figure(figsize=(20, 10))
    plt.axis('off')  # Turn off the axis
    
    # Sort locations and get corresponding colors
    sorted_indices = sorted(range(len(location_names)), 
                          key=lambda i: float(df[location_names[i]].iloc[-1]),
                          reverse=True)
    sorted_locations = [location_names[i] for i in sorted_indices]
    sorted_colors = [lines[i].get_color() for i in sorted_indices]
    
    # Add legend with matching colors
    plt.legend(handles=[plt.Line2D([0], [0], color=color, label=location) 
                       for location, color in zip(sorted_locations, sorted_colors)],
              loc='center',
              ncol=4,
              fontsize='small',
              title="Locations")
    
    # Save the legend separately
    plt.savefig('output/occupancy_legend.png', bbox_inches='tight', dpi=300)
    plt.close()

    # Create a separate plot for the top n legend
    plt.figure(figsize=(20, 10))
    plt.axis('off')  # Turn off the axis
    
    # Sort locations and get corresponding colors for top n
    n = 21
    sorted_indices_n = sorted(range(len(location_names)), 
                             key=lambda i: float(df[location_names[i]].iloc[-1]),
                             reverse=True)[:n]  # Take top n
    sorted_locations_n = [location_names[i] for i in sorted_indices_n]
    sorted_colors_n = [lines[i].get_color() for i in sorted_indices_n]
    
    # Add legend with matching colors for top n
    plt.legend(handles=[plt.Line2D([0], [0], color=color, label=location) 
                       for location, color in zip(sorted_locations_n, sorted_colors_n)],
              loc='center',
              ncol=3,  # Use 3 columns for n items
              fontsize='small',
              title=f"Top {n} Locations by Final Occupancy")
    
    # Save the top n legend separately
    plt.savefig(f'output/occupancy_legend_{n}.png', bbox_inches='tight', dpi=300)
    plt.close()

if __name__ == "__main__":
    # Read the data from saved files
    df = pd.read_csv('output/occupancy_df.csv', index_col=0)
    with open('output/location_names.txt', 'r') as f:
        location_names = [line.strip() for line in f.readlines()]
    draw_plot(df, location_names)