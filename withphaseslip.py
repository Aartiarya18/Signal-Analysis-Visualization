import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import tkinter as tk
from tkinter import filedialog, messagebox

# Function to load CSV file
def load_csv(title):
    file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
    if not file_path:
        return None, None
    try:
        # Parse the 'Time' column as datetime
        data = pd.read_csv(file_path, parse_dates=['Time'])
        print(f"Loaded file: {file_path}")  # Debugging
        return data['Time'], data['Carrier_Phase']
    except Exception as e:
        messagebox.showerror("Error", f"Failed to read file: {e}")
        return None, None

# Function to detect phase slips
def detect_phase_slips(carrier_phase, threshold=2.0):
    diffs = np.abs(np.diff(carrier_phase))
    slip_indices = np.where(diffs > threshold)[0] + 1  # Shift indices to match the actual slip location
    return slip_indices

# Function to plot data with phase slips
def plot_data(time, carrier_phase, title, color):
    if time is None or carrier_phase is None:
        print(f"No data for {title}")
        return
    
    slip_indices = detect_phase_slips(carrier_phase)
    
    plt.figure(figsize=(12, 6))
    plt.plot(time, carrier_phase, label=title, color=color, linewidth=2)
    plt.scatter(time.iloc[slip_indices], carrier_phase.iloc[slip_indices], color='red', s=50, label='Phase Slip', zorder=3)
    
    # Adjust x-axis formatting for better tick spacing
    plt.gca().xaxis.set_major_locator(mdates.HourLocator(interval=6))  # Show one tick every 6 hours
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M:%S'))  # Format timestamps
    
    plt.xlabel("Time")
    plt.ylabel("Carrier Phase")
    plt.title(title)
    plt.legend()
    plt.xticks(rotation=45)  # Rotate x-axis labels for readability
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.tight_layout()
    plt.show()

# Create Tkinter window
root = tk.Tk()
root.withdraw()

# # Load L9C Data
# time_L9C, carrier_phase_L9C = load_csv("Select L9C Data CSV")
# if time_L9C is not None:
#     plot_data(time_L9C, carrier_phase_L9C, "L9C Carrier Phase", "orange")

# # Load L5C Data
# time_L5C, carrier_phase_L5C = load_csv("Select L5C Data CSV")
# if time_L5C is not None:
#     plot_data(time_L5C, carrier_phase_L5C, "L5C Carrier Phase", "green")
