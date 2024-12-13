# app.py

from flask import Flask, render_template, request, jsonify
from route_optimizer import optimize_route
import pandas as pd
import os
import itertools

app = Flask(__name__)

# Load Aircraft Models
def load_aircraft_models(csv_path='Aircrafts.csv'):
    if not os.path.exists(csv_path):
        print(f"Error: {csv_path} not found.")
        return []
    try:
        df = pd.read_csv(csv_path)
        # Assuming the first column is 'Aircraft Model'
        aircraft_models = df['Aircraft Model'].dropna().unique().tolist()
        return aircraft_models
    except Exception as e:
        print(f"Error loading {csv_path}: {e}")
        return []

# Load Airports Data
def load_airports(csv_path='airports.csv'):
    if not os.path.exists(csv_path):
        print(f"Error: {csv_path} not found.")
        return []
    try:
        df = pd.read_csv(csv_path)
        # Ensure 'IATA', 'name', 'City', and 'Country' columns exist
        required_columns = {'Name', 'IATA', 'City', 'Country'}
        if not required_columns.issubset(df.columns):
            print(f"airports.csv must contain the following columns: {required_columns}")
            return []
        # Drop rows with missing IATA codes
        df = df.dropna(subset=['IATA'])
        # Create a list of dictionaries
        airports = df[['Name', 'IATA', 'City', 'Country']].to_dict(orient='records')
        print(f"Loaded {len(airports)} airports.")
        return airports
    except Exception as e:
        print(f"Error loading airports.csv: {e}")
        return []

# Preload data
AIRCRAFT_MODELS = load_aircraft_models()
AIRPORTS = load_airports()

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Retrieve form data
        selection_method = request.form.get('selection_method')
        source_input = request.form.get('source').strip()
        destination_input = request.form.get('destination').strip()
        date = request.form.get('date')

        # Initialize aircraft_model based on selection
        if selection_method == 'auto':
            aircraft_model = ""  # Empty string for automatic selection
            list_of_aircrafts = []  # Empty list indicates automatic selection
        elif selection_method == 'select':
            aircraft_model = request.form.get('aircraft_model')
            list_of_aircrafts = [aircraft_model] if aircraft_model else []
        else:
            aircraft_model = ""
            list_of_aircrafts = []

        # Input validation
        if not all([source_input, destination_input, date]):
            error = "Source, Destination, and Date fields are required."
            return render_template('index.html', error=error, aircraft_models=AIRCRAFT_MODELS, airports=AIRPORTS)

        # Additional validation if aircraft is selected from the list
        if selection_method == 'select' and not aircraft_model:
            error = "Please select an aircraft model or choose automatic selection."
            return render_template('index.html', error=error, aircraft_models=AIRCRAFT_MODELS, airports=AIRPORTS)

        # Extract IATA codes from source and destination inputs
        try:
            source_iata = extract_iata(source_input)
            destination_iata = extract_iata(destination_input)
            if not source_iata or not destination_iata:
                raise ValueError("Invalid Source or Destination Airport.")
        except Exception as e:
            error = f"Error processing airports: {str(e)}"
            return render_template('index.html', error=error, aircraft_models=AIRCRAFT_MODELS, airports=AIRPORTS)

        # Call the optimization algorithm
        try:
            optimization_result = optimize_route(
                source=source_iata,
                destination=destination_iata,
                aircraft_model=aircraft_model,
                date=date,
                list_of_aircrafts=list_of_aircrafts
            )
            best_route = optimization_result['best_route']
            total_cost = optimization_result['total_cost']
            total_distance = optimization_result['total_distance']
        except Exception as e:
            error = f"An error occurred during optimization: {str(e)}"
            return render_template('index.html', error=error, aircraft_models=AIRCRAFT_MODELS, airports=AIRPORTS)

        # Format the best route for display (e.g., as a list or a string)
        if best_route:
            result = f"Optimized Route: {best_route} | Total Cost: {total_cost:.2f} | Total Distance: {total_distance}km"
        else:
            result = "No route found."

        # Render the result
        return render_template('result.html', route=result)

    return render_template('index.html', aircraft_models=AIRCRAFT_MODELS, airports=AIRPORTS)

def extract_iata(input_str):
    """
    Extracts the IATA code from the input string.
    Expected format: "Airport Name (IATA)" or just "IATA"
    """
    if '(' in input_str and ')' in input_str:
        return input_str.split('(')[-1].split(')')[0].strip().upper()
    else:
        # If user enters just IATA code without the name
        return input_str.strip().upper()

@app.route('/autocomplete', methods=['GET'])
def autocomplete():
    query = request.args.get('q', '').strip().lower()
    if not query:
        return jsonify([])

    suggestions = []
    for airport in AIRPORTS:
        name = airport['Name']
        iata = airport['IATA']
        display = f"{name} ({iata})"
        if query in name.lower() or query in iata.lower():
            suggestions.append(display)
    return jsonify(suggestions)

if __name__ == '__main__':
    app.run(debug=True)
