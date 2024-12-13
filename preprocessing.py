import numpy as np
import pandas as pd
import json
from haversine import haversine_distance

iata_city_maps = pd.read_csv("airports.csv")
iata_city_maps = iata_city_maps[iata_city_maps["IATA"] != "\\N"]
iata_city_dict = dict(zip(iata_city_maps["IATA"], zip(iata_city_maps["City"], iata_city_maps["Country"], iata_city_maps["Latitude"], iata_city_maps["Longitude"])))


def create_aircrafts_dictionary(aircrafts_df, list_of_aircrafts):
    aircrafts_dict = {}
    for _, row in aircrafts_df.iterrows():
        range_str = str(row['Max Range (NM)']).replace(',', '').replace('NM', '').replace('nm', '').strip()
        if '/' in range_str:
            range_str = range_str.split('/')[0].strip()
        range_km = round(float(range_str) * 1.852, 2)
        if pd.isna(row["Max Operation Mach No"]):
            mach_values = aircrafts_df["Max Operation Mach No"].dropna()
            avg_mach = mach_values.mean()
            row["Max Operation Mach No"] = round(avg_mach, 2)

        aircrafts_dict[row["Aircraft Model"]] = (range_km, row["Max Operation Mach No"])

    if len(list_of_aircrafts) == 0: #The user has given no input
        return aircrafts_dict
    else: #The user has given a list of aircrafts a input
        user_aircrafts_dict = {}
        for model in list_of_aircrafts:
            user_aircrafts_dict[model] = aircrafts_dict[model]
        return user_aircrafts_dict
    
def create_routes_dictionary(airline_routes):
    route_info_dict = {}
    for index, key in enumerate(airline_routes.keys()):
        airport_data = airline_routes[key]
        city = airport_data['city_name']
        country = airport_data['country']
        airport_name = airport_data['name']

        routes_list = []

        for route in airport_data['routes']:
            destination_city = iata_city_dict.get(route['iata'], None)
            if destination_city == None:
                continue
            destination_city = destination_city[0]
            destination_city_iata = route['iata']
            destination_country = iata_city_dict[route['iata']][1]
            travel_distance = route['km']
            travel_time = route['min']
            destination_latitude = iata_city_dict[route["iata"]][2]
            destination_longitude = iata_city_dict[route["iata"]][3]

            route_tuple = (
                destination_city,
                destination_city_iata,
                destination_latitude,
                destination_longitude,
                destination_country,
                travel_distance,
                travel_time
            )
            routes_list.append(route_tuple)
            route_info_dict[key] = routes_list
    return route_info_dict


def create_cost_distance_matrix(route_info_dict, airports, airline_routes):
    print("* Creating the cost and distance matrices...\n")
    n_airports = len(airports)
    iata_to_index = {iata: idx for idx, iata in enumerate(airports)}
    cost_matrix = np.zeros((n_airports, n_airports)) #Initializing the cost matrix with zeroes.
    distance_matrix = np.zeros((n_airports, n_airports)) # This matrix will contain the distances only. (For use in fitness function)
    np.fill_diagonal(cost_matrix, -1) #Diagonals (self-connections) are -1

    for source_iata, routes in route_info_dict.items():
        source_idx = iata_to_index[source_iata]
        for route in routes:
            # ('Faaite', 'FAC', -16.68670082, -145.3289948, 'French Polynesia', 76, 20) This is a sample route.
            destination_iata = route[1]
            if destination_iata in iata_to_index:
                destination_index = iata_to_index[destination_iata]
                distance = route[5]
                time = route[6]
                
                cost = distance + time #Might adjust later

                distance_matrix[source_idx][destination_index] = distance
                distance_matrix[destination_index][source_idx] = distance
                #Assuming that the matrix is symmetric (A -> B == B -> A)
                cost_matrix[source_idx][destination_index] = cost
                cost_matrix[destination_index][source_idx] = cost

    #Unknowns will be filled with calculated distances using lati and long.
    for i in range(n_airports):
        for j in range(i + 1, n_airports):
            if cost_matrix[i][j] == 0:
                source_iata = airports[i]
                destination_iata = airports[j]

                source_latitude = float(airline_routes[source_iata]["latitude"])
                source_longitude = float(airline_routes[source_iata]["longitude"])

                destination_latitude = float(airline_routes[destination_iata]["latitude"])
                destination_longitude = float(airline_routes[destination_iata]["longitude"])

                distance = haversine_distance(source_latitude, source_longitude, destination_latitude, destination_longitude)
                estimated_time = (distance / 800) * 60
                # print(f"Distance: {distance} and Time: {estimated_time}")
                cost = distance + estimated_time

                distance_matrix[i][j] = distance
                distance_matrix[j][i] = distance

                cost_matrix[i][j] = cost
                cost_matrix[j][i] = cost
    return cost_matrix, distance_matrix



# Uncomment to save the cost matrix to a CSV file:

# cost_matrix_df = pd.DataFrame(cost_matrix, index=airports, columns=airports)
# cost_matrix_df.to_csv('cost_matrix.csv')
# print("Preview of the saved matrix:")
# print(cost_matrix_df.iloc[:5, :5])