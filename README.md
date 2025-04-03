# Signal Analysis Visualization

## Overview
Signal Analysis Visualization is a Flask-based web application for processing and visualizing RINEX observation data. The application extracts GNSS signal parameters, processes the data, and generates carrier phase graphs with phase slip detection.

## Features
- **File Upload**: Supports multiple RINEX observation files for processing.
- **Signal Extraction**: Parses GNSS signals including GPS, GLONASS, Galileo, and more.
- **Data Processing**:
  - Converts raw observations into structured tabular format.
  - Computes carrier phase for single and dual frequencies.
- **Visualization**:
  - Single and double carrier phase graphs.
  - Phase slip detection with highlighted points.
- **Downloadable CSV Output**: Processed data can be exported for further analysis.

## Technologies Used
- **Backend**: Python, Flask
- **Frontend**: HTML, CSS (Bootstrap), JavaScript
- **Data Processing**: NumPy, Pandas
- **Visualization**: Matplotlib

## Installation
### Prerequisites
Ensure you have Python 3.x installed.

### Clone the Repository
```bash
git clone https://github.com/your-username/signal-analysis-visualization.git
cd signal-analysis-visualization
```

### Install Dependencies
```bash
pip install -r requirements.txt
```

## Running the Application
```bash
python app.py
```
The application will be accessible at `http://127.0.0.1:5000/`.

## Usage
1. Upload RINEX observation files.
2. Process the files to extract GNSS observation data.
3. Select a satellite and observation type to analyze.
4. Generate carrier phase graphs with or without phase slip detection.
5. Download processed CSV data for further use.

## Folder Structure
```
├── app.py                 # Main Flask application
├── templates/             # HTML templates
│   ├── upload.html
│   ├── csv.html
│   ├── graph.html
├── static/                # Static files (CSS, JavaScript, Images)
├── uploads/               # Directory for uploaded files
├── processed/             # Directory for processed CSV files
├── requirements.txt       # Dependencies
├── README.md              # Project documentation
```

## API Endpoints
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET, POST | Upload RINEX files |
| `/csv` | GET, POST | Process and extract data |
| `/graph` | GET | View graphs |
| `/generate_graph` | POST | Generate graphs with selected parameters |

## License
This project is licensed under the MIT License.

## Author
Developed by **[Your Name]**

## Contributions
Contributions are welcome! Feel free to fork the repository and submit a pull request.

## Acknowledgments
- RINEX format documentation
- Matplotlib & Pandas for data visualization and processing

