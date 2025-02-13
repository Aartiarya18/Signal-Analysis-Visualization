import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import tkinter as tk
from tkinter import filedialog, messagebox

# Function to open file dialog and select CSV
def select_file():
    root = tk.Tk()
    root.withdraw()  # Hide the root window
    file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
    
    if not file_path:
        messagebox.showerror("Error", "No file selected! Exiting...")
        exit()
    return file_path

# File selection
file_path = select_file()

# Reading the CSV file
try:
    df = pd.read_csv(file_path)
    
    # Validate the presence of required columns
    if 'Time' not in df.columns or 'Carrier_Phase' not in df.columns:
        raise ValueError("The CSV file must contain 'Time' and 'Carrier_Phase' columns.")
except Exception as e:
    messagebox.showerror("File Error", f"Error reading file: {str(e)}")
    exit()

# Convert 'Time' column to datetime
df['Time'] = pd.to_datetime(df['Time'], errors='coerce')

# Drop invalid datetime rows
df = df.dropna(subset=['Time'])

# Filter data for the last 3 days
latest_time = df['Time'].max()  # Find the most recent timestamp in the dataset
three_days_ago = latest_time - pd.Timedelta(days=3)
df_filtered = df[df['Time'] >= three_days_ago]

# Check if there is data for the last 3 days
if df_filtered.empty:
    messagebox.showwarning("No Data", "No data available for the last 3 days.")
    exit()

# Plotting
plt.figure(figsize=(12, 6))
plt.plot(df_filtered['Time'], df_filtered['Carrier_Phase'], color='blue', label='Carrier Phase (Last 3 Days)')
plt.xlabel('Time')
plt.ylabel('Carrier Phase(Kilometer)')
plt.title('Carrier Phase over the Time')

# Formatting the x-axis
plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M:%S'))
plt.gca().xaxis.set_major_locator(mdates.AutoDateLocator())

# Rotate and adjust ticks
plt.xticks(rotation=45)
plt.legend()
plt.grid()

# Optimize layout
plt.tight_layout()

# Show the plot
plt.show()
