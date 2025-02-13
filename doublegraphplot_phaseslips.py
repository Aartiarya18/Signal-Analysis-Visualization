import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import tkinter as tk
from tkinter import filedialog, messagebox

def validate_and_load_file():
        """Prompt user to select a CSV file, validate its structure, and load it into a DataFrame."""
        root = tk.Tk()
        root.withdraw()  # Hide the main Tkinter window
        
        file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        
        if not file_path:
            messagebox.showwarning("No File Selected", "Please select a CSV file.")
            return None

        try:
            df = pd.read_csv(file_path)
            required_columns = {"Time", "Carrier_Phase_1", "Carrier_Phase_2"}
            if not required_columns.issubset(df.columns):
                messagebox.showerror("Invalid File", "The selected file must contain 'Time', 'Carrier_Phase_1', and 'Carrier_Phase_2' columns.")
                return None

            df['Time'] = pd.to_datetime(df['Time'], format='%Y-%m-%d %H:%M:%S', errors='coerce')
            if df['Time'].isna().sum() > 0:
                messagebox.showerror("Invalid Time Format", "Some timestamps could not be parsed. Ensure the 'Time' column is formatted correctly.")
                return None

            messagebox.showinfo("Success", "File loaded successfully!")
            return df
        
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred while loading the file:\n{e}")
            return None

df = validate_and_load_file()
if df is not None:
        threshold = 5  # Adjust threshold for phase slips
        df['Phase_Slip_1'] = df['Carrier_Phase_1'].diff().abs() > threshold
        df['Phase_Slip_2'] = df['Carrier_Phase_2'].diff().abs() > threshold

        fig, ax = plt.subplots(figsize=(12, 6))
        ax.plot(df['Time'], df['Carrier_Phase_1'], label='Carrier Phase 1', color='orange')
        ax.plot(df['Time'], df['Carrier_Phase_2'], label='Carrier Phase 2', color='skyblue')
        
        ax.scatter(df['Time'][df['Phase_Slip_1']], df['Carrier_Phase_1'][df['Phase_Slip_1']], color='red', label='Phase Slips 1', zorder=3)
        ax.scatter(df['Time'][df['Phase_Slip_2']], df['Carrier_Phase_2'][df['Phase_Slip_2']], color='red', label='Phase Slips 2', zorder=3)
        
        ax.set_xlabel("Time")
        ax.set_ylabel("Carrier Phase Kilometer")
        ax.set_title("Carrier Phase with Phase Slips")
        ax.legend()
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M:%S'))
        plt.xticks(rotation=45)
        plt.grid()
        plt.show()
