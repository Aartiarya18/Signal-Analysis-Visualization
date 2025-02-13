import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import tkinter as tk
from tkinter import filedialog, messagebox

def validate_and_load_file():
    # Prompt the user to select a CSV file
    file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
    if not file_path:
        return None

    try:
        # Load the CSV file into a DataFrame
        df = pd.read_csv(file_path)

        # Check for required columns
        required_columns = ['Time', 'Carrier_Phase_1', 'Carrier_Phase_2']
        if not all(col in df.columns for col in required_columns):
            messagebox.showerror("Error", f"The file must contain the following columns: {', '.join(required_columns)}")
            return None

        # Ensure Time column is in the correct format
        try:
            df['Time'] = pd.to_datetime(df['Time'], format='%Y-%m-%d %H:%M:%S')
        except Exception as e:
            messagebox.showerror("Error", f"'Time' column is not in the correct format (YYYY-MM-DD HH:MM:SS).\nDetails:\n{e}")
            return None

        return df

    except Exception as e:
        messagebox.showerror("Error", f"An error occurred while loading the file:\n{e}")
        return None

def plot_data():
    # Load and validate the CSV file
    df = validate_and_load_file()
    if df is None:
        return

    try:
        # Plot Carrier Phase for two frequencies
        plt.figure(figsize=(12, 6))
        plt.plot(df['Time'], df['Carrier_Phase_1'], label='Frequency 1', color='blue', marker='o')
        plt.plot(df['Time'], df['Carrier_Phase_2'], label='Frequency 2', color='orange', marker='x')

        # Customize the plot
        plt.title("Carrier Phase over Time")
        plt.xlabel("Time")
        plt.ylabel("Carrier Phase (Kilometers)")
        plt.legend()
        plt.grid(True)

        # Explicitly format the time axis
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M:%S'))
        plt.gca().xaxis.set_major_locator(mdates.AutoDateLocator())
        plt.gcf().autofmt_xdate()  # Rotate date labels for better visibility

        # Show the plot
        plt.tight_layout()
        plt.show()

    except Exception as e:
        messagebox.showerror("Error", f"An error occurred while plotting the data:\n{e}")

# Create the main Tkinter window
root = tk.Tk()
root.title("Carrier Phase Plotter")

# Create a button to select and plot the CSV data
plot_button = tk.Button(root, text="Select CSV and Plot Data", command=plot_data)
plot_button.pack(pady=20)

# Run the Tkinter main loop
root.mainloop()
