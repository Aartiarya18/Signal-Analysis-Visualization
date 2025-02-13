import os
import subprocess
import time
import numpy as np
import pandas as pd
from flask import Flask, request, render_template, render_template_string, jsonify, redirect, url_for, send_file
import matplotlib
import matplotlib.pyplot as plt
matplotlib.use("TkAgg")  # Use Tkinter backend
import matplotlib.dates as mdates
import tkinter as tk
from tkinter import filedialog, messagebox
matplotlib.use('Agg')  # Use Agg backend to avoid GUI-related issues

app = Flask(__name__)

# Ensure the static folder exists
if not os.path.exists('static'):
    os.makedirs('static')
UPLOAD_FOLDER = "uploads"
PROCESSED_FOLDER = "processed"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)

#--------------------Script for Upload.html--------------------
class Receiver:
    def __init__(self):
        self.rinex_version = None
        self.observation_type = ""
        self.system_type = ""
        self.observation_codes = {}
        self.observation_data = []
        self.epochs = []

    def _parse_rinex_version_type_line(self, line):
        self.rinex_version = float(line[:9].strip())
        self.observation_type = line[20:40].strip()
        system_char = line[40:41].strip()
        system_map = {'G': 'GPS', 'R': 'GLONASS', 'S': 'SBAS', 'E': 'Galileo',
                      'J': 'QZSS', 'C': 'BDS', 'I': 'IRNSS', 'M': 'Mixed'}
        self.system_type = system_map.get(system_char, system_char)

    def _parse_sys_obs_types_line(self, line):
        parts = line.split()
        if len(parts) < 2:
            return
        system = parts[0]
        num_obs_types = int(parts[1]) if parts[1].isdigit() else 0
        obs_types = parts[2:2 + num_obs_types]
        self.observation_codes[system] = obs_types

    def _parse_epoch_line(self, line):
        parts = line[1:].split()
        year, month, day, hour, minute = map(int, parts[:5])
        second = float(parts[5])
        epoch_time = np.datetime64(f'{year:04d}-{month:02d}-{day:02d}T{hour:02d}:{minute:02d}:{int(second):02d}')
        self.epochs.append(epoch_time)
        return epoch_time

    def _parse_prn_obs_line(self, epoch, line):
        prn = line[:3].strip()
        if not prn:
            return
        gnss_system = prn[0]
        obs_types = self.observation_codes.get(gnss_system, [])
        data_start, data_length = 3, 16

        for obs_type in obs_types:
            data_end = data_start + data_length
            data_point = line[data_start:data_end].strip()
            try:
                value = float(data_point[:-2]) if len(data_point) > 2 else None
            except ValueError:
                value = None

            self.observation_data.append({
                'Epoch': epoch,
                'Obs_Type': obs_type,
                'PRN': prn,
                'GNSS_System': gnss_system,
                'Value': value
            })
            data_start = data_end

    def import_data(self, filepath):
        obs_data_start, current_epoch = False, None
        try:
            with open(filepath, 'r') as file:
                for line in file:
                    if 'END OF HEADER' in line:
                        obs_data_start = True
                        continue
                    if line.startswith('>'):
                        current_epoch = self._parse_epoch_line(line)
                    elif obs_data_start:
                        self._parse_prn_obs_line(current_epoch, line)
                    elif 'SYS / # / OBS TYPES' in line:
                        self._parse_sys_obs_types_line(line)
        except Exception as e:
            print(f"Error processing file {filepath}: {str(e)}")

    def export_data(self, output_file):
        if not self.observation_data:
            print("No data found to export.")
            return

        df = pd.DataFrame(self.observation_data)
        df = df.sort_values(by="Epoch")  # Sorting timewise (Epochwise)
        df.to_csv(output_file, index=False, sep='\t')

def process_uploaded_files(file_paths):
    receiver = Receiver()
    for file_path in file_paths:
        receiver.import_data(file_path)
    
    timestamp = int(time.time())
    processed_file = os.path.join(PROCESSED_FOLDER, f"processed_{timestamp}.txt")
    receiver.export_data(processed_file)
    return processed_file

# Declare processed_file as a global variable
processed_file = None

@app.route('/', methods=['GET', 'POST'])
def upload_page():
    global processed_file  # 🔴 Declare global variable
    if request.method == 'POST':
        if 'file' not in request.files:
            return "No file uploaded", 400  # 🔴 This is causing the issue.

        uploaded_files = request.files.getlist('file')  # 🔄 Get multiple files

        if not uploaded_files or all(f.filename == '' for f in uploaded_files):
            return "No selected file", 400

        file_paths = []
        for uploaded_file in uploaded_files:
            if uploaded_file.filename:  # 🟢 Ensure filename exists
                file_path = os.path.join(UPLOAD_FOLDER, uploaded_file.filename)
                uploaded_file.save(file_path)
                file_paths.append(file_path)

        if not file_paths:
            return "No valid files uploaded", 400

        # Process files
        processed_file = process_uploaded_files(file_paths)
        return redirect(url_for('csv_page'))
    
    return render_template('upload.html')

#--------------------Script for csv.html--------------------
C = 299792458  # Speed of light in m/s
F1 = 1575.42e6  # Frequency for L1 in Hz
F2 = 1227.60e6  # Frequency for L2 in Hz
F5 = 1176.45e6  # Frequency for L5 in Hz
F9 = 2492.028e6  # Frequency for L9 in Hz

default_frequency_mapping = {
    "L1C": F1, "L2C": F2, "L5C": F5, "C5C": F5, "L5C": F5, "D5C": F5, "S5C": F5,
    "C9C": F9, "L9C": F9, "D9C": F9, "S9C": F9, "P1": F1, "P2": F2, "P5": F5,
    "L1L": F1, "L2L": F2
}


def load_large_observation_file(file_path):
    if not os.path.isfile(file_path):
        return None
    df = pd.read_csv(file_path, sep="\t", engine='python', dtype=str)
    df.columns = df.columns.str.strip().str.upper()
    df['EPOCH'] = pd.to_datetime(df['EPOCH'], errors='coerce')
    df.sort_values(by='EPOCH', inplace=True)
    return df


def search_carrier_data(df, satellite, observation_type, output_csv_path):
    satellite = satellite.upper()
    observation_type = observation_type.upper()

    result = df[(df['OBS_TYPE'] == observation_type) & (df['PRN'] == satellite)].copy()

    if not result.empty:
        frequency = default_frequency_mapping.get(observation_type, None)
        if frequency is None:
            return None

        result['VALUE'] = pd.to_numeric(result['VALUE'], errors='coerce')
        result['Distance'] = result['VALUE'].apply(lambda x: -(C * x) / (frequency * 1000) if pd.notna(x) else None)
        result = result[['EPOCH', 'Distance']]
        result.rename(columns={'EPOCH': 'Time', 'Distance': 'Carrier_Phase'}, inplace=True)
        result.to_csv(output_csv_path, index=False)
        return output_csv_path
    return None

def search_carrier_data(df, satellite, observation_type, output_csv_path):
    """Processes Single Carrier Phase Data"""
    satellite = satellite.upper()
    observation_type = observation_type.upper()

    result = df[(df['OBS_TYPE'] == observation_type) & (df['PRN'] == satellite)].copy()

    if not result.empty:
        frequency = default_frequency_mapping.get(observation_type, None)
        if frequency is None:
            return None

        result['VALUE'] = pd.to_numeric(result['VALUE'], errors='coerce')
        result['Carrier_Phase'] = result['VALUE'].apply(lambda x: -(C * x) / (frequency * 1000) if pd.notna(x) else None)
        result = result[['EPOCH', 'Carrier_Phase']]
        result.rename(columns={'EPOCH': 'Time'}, inplace=True)
        result.to_csv(output_csv_path, index=False)
        return output_csv_path
    return None


def search_double_carrier_data(df, satellite, observation_type_1, observation_type_2, output_csv_path):
    """Processes Double Carrier Phase Data"""
    satellite = satellite.upper()
    observation_type_1 = observation_type_1.upper()
    observation_type_2 = observation_type_2.upper()

    result1 = df[(df['OBS_TYPE'] == observation_type_1) & (df['PRN'] == satellite)].copy()
    result2 = df[(df['OBS_TYPE'] == observation_type_2) & (df['PRN'] == satellite)].copy()

    if not result1.empty and not result2.empty:
        freq1 = default_frequency_mapping.get(observation_type_1, None)
        freq2 = default_frequency_mapping.get(observation_type_2, None)
        if freq1 is None or freq2 is None:
            return None

        result1['VALUE'] = pd.to_numeric(result1['VALUE'], errors='coerce')
        result2['VALUE'] = pd.to_numeric(result2['VALUE'], errors='coerce')

        result1['Carrier_Phase_1'] = result1['VALUE'].apply(lambda x: -(C * x) / (freq1 * 1000) if pd.notna(x) else None)
        result2['Carrier_Phase_2'] = result2['VALUE'].apply(lambda x: -(C * x) / (freq2 * 1000) if pd.notna(x) else None)

        merged_result = pd.merge(result1[['EPOCH', 'Carrier_Phase_1']], result2[['EPOCH', 'Carrier_Phase_2']], on='EPOCH', how='inner')
        merged_result.rename(columns={'EPOCH': 'Time'}, inplace=True)

        merged_result.to_csv(output_csv_path, index=False)
        return output_csv_path
    return None

generated_csv_file = None  # Declare a global variable

@app.route('/csv', methods=['GET', 'POST'])
def csv_page():
    global generated_csv_file  # Use the global variable
    if request.method == 'POST':
        satellite = request.form["satellite"]
        observation_type_1 = request.form["observation_type_1"]
        mode = request.form["mode"]  # Get single/double mode
        
        observation_type_2 = request.form.get("observation_type_2", None) if mode == "double" else None

        timestamp = int(time.time())
        generated_csv_file = os.path.join(PROCESSED_FOLDER, f"csv_{timestamp}.csv")
        df = load_large_observation_file(processed_file)

        if df is not None:
            if mode == "single":
                csv_file = search_carrier_data(df, satellite, observation_type_1, generated_csv_file)
            else:
                csv_file = search_double_carrier_data(df, satellite, observation_type_1, observation_type_2, generated_csv_file)

            if csv_file:
                return redirect(url_for('graph_page', type=mode))  # Pass mode in URL

    return render_template('csv.html')

#--------------------Script for graph.html--------------------
class GraphPlotter:
    def __init__(self, mode='single'):
        global generated_csv_file
        self.file_path = generated_csv_file  # Use latest generated file
        self.mode = mode
        self.df = self.load_csv()  # Ensure CSV is loaded properly

    def load_csv(self):
        try:
            df = pd.read_csv(self.file_path)
            print("Debug CSV Read:", df.head())  # Debugging: Print first few rows

            # Check column names (trim spaces if needed)
            df.columns = df.columns.str.strip()

            # Ensure 'Time' column is parsed correctly
            if 'Time' in df.columns:
                df['Time'] = pd.to_datetime(df['Time'], errors='coerce')
            else:
                print("Error: 'Time' column not found in CSV.")
            return df
        except Exception as e:
            messagebox.showerror("Error", f"Failed to read file: {e}")
            return None

    def detect_phase_slips(self, carrier_phase, threshold=2.0):
        diffs = np.abs(np.diff(carrier_phase))
        return np.where(diffs > threshold)[0] + 1  # Adjust indices

    def plot_graph(self, title, color, detect_phase=False):
        if self.df is None:
            return
        
        print("✅ CSV Loaded Successfully!")
        print("📌 Columns in CSV:", self.df.columns)
        print("📊 Data Types:\n", self.df.dtypes)
        print("📝 Sample Data:\n", self.df.head())

        plt.figure(figsize=(12, 6))
        time = self.df['Time']

        if self.mode == 'single':
            if 'Carrier_Phase' in self.df.columns:
                carrier_phase = pd.to_numeric(self.df['Carrier_Phase'], errors='coerce')
                plt.plot(time, carrier_phase, label=title, color=color, linewidth=2)

                if detect_phase:
                    slip_indices = self.detect_phase_slips(carrier_phase)
                    plt.scatter(time.iloc[slip_indices], carrier_phase.iloc[slip_indices], color='red', s=50, label='Phase Slip', zorder=3)
            else:
                print("Error: 'Carrier_Phase' column not found in the CSV file.")

        else:  # Double Mode
            try:
                print("Available columns in DataFrame:", self.df.columns)  # Debugging step

                if 'Carrier_Phase_1' in self.df.columns and 'Carrier_Phase_2' in self.df.columns:
                    carrier_phase_1 = pd.to_numeric(self.df['Carrier_Phase_1'], errors='coerce')
                    carrier_phase_2 = pd.to_numeric(self.df['Carrier_Phase_2'], errors='coerce')

                    plt.plot(time, carrier_phase_1, label="Carrier Phase 1", color="blue", linewidth=2)
                    plt.plot(time, carrier_phase_2, label="Carrier Phase 2", color="green", linewidth=2)

                    if detect_phase:
                        slip_indices_1 = self.detect_phase_slips(carrier_phase_1)
                        slip_indices_2 = self.detect_phase_slips(carrier_phase_2)

                        plt.scatter(time.iloc[slip_indices_1], carrier_phase_1.iloc[slip_indices_1], color='red', s=50, label='Phase Slip 1', zorder=3)
                        plt.scatter(time.iloc[slip_indices_2], carrier_phase_2.iloc[slip_indices_2], color='purple', s=50, label='Phase Slip 2', zorder=3)
                else:
                    print("Error: 'Carrier_Phase_1' and/or 'Carrier_Phase_2' column(s) not found in the CSV file.")

            except KeyError as e:
                print(f"Error: {e}. Check if CSV contains 'Carrier_Phase_1' and 'Carrier_Phase_2'.")

        plt.xlabel("Time")
        plt.ylabel("Carrier Phase")
        plt.title(title)
        plt.legend()
        plt.xticks(rotation=45)
        plt.grid(True, linestyle="--", alpha=0.6)
        plt.tight_layout()
        plt.savefig("static/graph.png")
        return send_file("static/graph.png", mimetype="image/png")

@app.route('/graph', methods=['GET'])
def graph_page():
    graph_type = request.args.get('type', 'single')  # Default to single
    html_content = render_template('graph.html', graph_type=graph_type)
    return render_template_string(html_content)

@app.route('/generate_graph', methods=['POST'])
def generate_graph():
    graph_type = request.form.get("graph_type")
    mode = request.args.get("type", "single")  # Detect if single or double
    plotter = GraphPlotter(mode=mode)

    if graph_type == "sgraph_no_phase":
        plotter.plot_graph("Single Graph without Phase Slip", "blue", detect_phase=False)
    elif graph_type == "sgraph_with_phase":
        plotter.plot_graph("Single Graph with Phase Slip", "blue", detect_phase=True)
    elif graph_type == "dgraph_no_phase":
        plotter.plot_graph("Double Graph without Phase Slip", "blue", detect_phase=False)
    elif graph_type == "dgraph_with_phase":
        plotter.plot_graph("Double Graph with Phase Slip", "blue", detect_phase=True)
    else:
        return jsonify({"success": False, "message": "Invalid graph type selected."})

    return jsonify({"success": True, "message": "Graph generated successfully."})



if __name__ == '__main__':
    app.run(debug=True)