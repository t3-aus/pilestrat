import numpy as np
import pandas as pd

def evaluate_stockpile_geometries(config_mode="Standard Production"):
    """
    Evaluates bulk agricultural stockpile geometries under specified Configuration Modes.
    """
    # Define extended candidate geometries including new modular variants
    geometries = [
        {"Geometry": "Windrow", "Height": 3.0, "Max_Depth": 1.8, "Volume": 172727, "Uniformity": 0.93, "Pressure_Drop": 0.160},
        {"Geometry": "Ribbon", "Height": 4.0, "Max_Depth": 2.0, "Volume": 172727, "Uniformity": 0.92, "Pressure_Drop": 0.280},
        {"Geometry": "Modular Cell", "Height": 5.0, "Max_Depth": 2.5, "Volume": 172727, "Uniformity": 0.90, "Pressure_Drop": 0.413},
        {"Geometry": "Hybrid", "Height": 4.5, "Max_Depth": 2.2, "Volume": 172727, "Uniformity": 0.91, "Pressure_Drop": 0.338},
        {"Geometry": "Flat Deck", "Height": 3.5, "Max_Depth": 3.5, "Volume": 172727, "Uniformity": 0.86, "Pressure_Drop": 0.368},
        {"Geometry": "Rectangular", "Height": 6.0, "Max_Depth": 4.0, "Volume": 172727, "Uniformity": 0.84, "Pressure_Drop": 0.780},
        {"Geometry": "Asymmetric Block", "Height": 3.8, "Max_Depth": 2.1, "Volume": 172727, "Uniformity": 0.91, "Pressure_Drop": 0.295}, # Added geometry
        {"Geometry": "Dual-Tier Ribbon", "Height": 4.2, "Max_Depth": 2.2, "Volume": 172727, "Uniformity": 0.89, "Pressure_Drop": 0.310}, # Added geometry
        {"Geometry": "Conical", "Height": 8.0, "Max_Depth": 8.0, "Volume": 172727, "Uniformity": 0.68, "Pressure_Drop": 2.160},
        {"Geometry": "Mega Pile", "Height": 12.0, "Max_Depth": 12.0, "Volume": 172727, "Uniformity": 0.52, "Pressure_Drop": 5.910}
    ]
    
    df = pd.DataFrame(geometries)
    
    # Configuration Mode adjustments
    fan_limit = 2.5  # kPa
    if config_mode == "High-Density Winter":
        # Stricter weighting for pressure drop and pathogen reduction in cold, humid conditions
        df['Pathogen_Reduction'] = np.clip(df['Uniformity'] * 98.5 - (df['Pressure_Drop'] * 2.0), 40, 95)
        df['TPI_Score'] = (df['Uniformity'] * 50) + ((fan_limit - np.minimum(df['Pressure_Drop'], fan_limit)) / fan_limit * 30) + (df['Pathogen_Reduction'] * 0.2)
    elif config_mode == "Rapid Harvest Intake":
        # Prioritize throughput and volume-handling capacity
        df['Pathogen_Reduction'] = np.clip(df['Uniformity'] * 95.0, 45, 92)
        df['TPI_Score'] = (df['Uniformity'] * 40) + ((fan_limit - np.minimum(df['Pressure_Drop'], fan_limit)) / fan_limit * 20) + (df['Pathogen_Reduction'] * 0.4)
    else:
        # Standard Production Mode
        df['Pathogen_Reduction'] = np.clip(df['Uniformity'] * 98.5, 50, 95)
        df['TPI_Score'] = (df['Uniformity'] * 45) + ((fan_limit - np.minimum(df['Pressure_Drop'], fan_limit)) / fan_limit * 25) + (df['Pathogen_Reduction'] * 0.3)
        
    df['Fan_Feasible'] = df['Pressure_Drop'] <= fan_limit
    
    return df.sort_values(by="TPI_Score", ascending=False).reset_index(drop=True)

# Execute simulation with Configuration Mode selected
active_mode = "High-Density Winter"
results_df = evaluate_stockpile_geometries(config_mode=active_mode)
print(f"--- Simulation Results: Configuration Mode [{active_mode}] ---")
print(results_df[['Geometry', 'Height', 'Max_Depth', 'Pressure_Drop', 'Fan_Feasible', 'TPI_Score']])
