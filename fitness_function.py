import weatherapi, os, json
from pprint import pprint
from dotenv import load_dotenv
load_dotenv()

configuration = weatherapi.Configuration()
configuration.api_key['key'] = os.getenv("WEATHER_API_KEY")
api_instance = weatherapi.APIsApi(weatherapi.ApiClient(configuration))

with open("airline_routes.json", "r") as file:
    airline_routes = json.load(file)

def get_weather_information(latitude, longitude):
    q = str(latitude) + "," + str(longitude) #This is a parameter for the API. It MUST be in this format --> "lat,long"
    try:
        api_response = api_instance.realtime_weather(q)
        weather_info = {
            "temperature": api_response["current"]["temp_c"],
            "humidity": api_response["current"]["humidity"],
            "wind_speed": api_response["current"]["wind_kph"],
            "visibility": api_response["current"]["vis_km"],
            "precipitation": api_response["current"]["precip_mm"],
        }
    except Exception as e:
        print("Exception when requesting weather from API: ", e)
        return None
    
    return weather_info

def calculate_route_cost(route, cost_matrix, distance_matrix, iata_to_index, aircrafts_dict, iata_to_lat_long = airline_routes):
    total_cost = 0
    origin_index = iata_to_index[route[1]]
    destination_index = iata_to_index[route[-1]]
    # print(f"Total distance to travel: {distance_matrix[origin_index][destination_index]}kms")
    aircraft = route[0][0]
    aircraft_range = aircrafts_dict[aircraft][0]
    aircraft_mach_no = aircrafts_dict[aircraft][1]
    # print(f"{aircraft} Range: {aircraft_range} and Mach: {aircraft_mach_no}")
    route_distance = 0
    #If its a direct flight, then compare the distance with aircraft's range. If distance > range then increase cost Massively.
    if len(route) == 3 and distance_matrix[origin_index][destination_index] > aircraft_range:
        print(f"Direct flight between {route[1]} and {route[-1]} not possible because Direct distance = {distance_matrix[origin_index][destination_index]}kms and Aircraft's range = {aircraft_range}kms")
        total_cost = 150000
        return total_cost
    for i in range(1, len(route) - 1):
        source = route[i]
        source_latitude = iata_to_lat_long[source]["latitude"]
        source_longitude = iata_to_lat_long[source]["longitude"]
        # print("Fetching Location information!")
        weather_info = get_weather_information(source_latitude, source_longitude)
        if weather_info:
            temp_penalty = abs(weather_info.get("temperature", 15)) * 50
            humidity_penalty = weather_info.get("humidity", 50) * 100
            wind_penalty = weather_info.get("wind_speed", 10.0) * 100
            visibility_penalty = 3000 if weather_info.get("visibility", 10) < 5.0 else 0
            precipitation_penalty = weather_info.get("precipitation", 0.0) * 1000
            
            total_weather_penalty = (
                temp_penalty +
                humidity_penalty +
                wind_penalty +
                visibility_penalty +
                precipitation_penalty
            )
            if total_weather_penalty > 15000:  # Threshold for extreme weather penalties
                print(f"Extreme Weather Penalty Detected for {source}: {total_weather_penalty}\n"
                      f"(Temperature: {weather_info["temperature"]} C\nHumidity: {weather_info['humidity']}\n"
                      f"Wind: {weather_info['wind_speed']}kph\nVisibility: {weather_info['visibility']}kms\nPrecipitation: {weather_info['precipitation']}mm)\n")

        destination = route[i + 1]
        source_index = iata_to_index[source]
        destination_index = iata_to_index[destination]

        #Calculating the range between two cities. If its higher than the total range of the aircraft then increase the cost massively.
        immediate_distance = distance_matrix[source_index][destination_index]
        if immediate_distance > aircraft_range:
            # print("\t Inefficient Route")
            total_cost += 1000
        else:
            # Reduce cost if aircraft has more range than needed
            # print("\t Efficient Route")
            range_efficiency = (aircraft_range - immediate_distance) / aircraft_range
            total_cost *= (1 - range_efficiency * 0.2)  # Reduce cost by up to 50% based on efficiency
        
        
        route_distance += distance_matrix[source_index][destination_index]
        total_cost += cost_matrix[source_index][destination_index]

    #Getting the weather information of destination
    # print("Fetching destination weather information")
    weather_info_destination = get_weather_information( iata_to_lat_long[route[-1]]["latitude"], iata_to_lat_long[route[-1]]["longitude"] )
    if weather_info_destination:
        temp_penalty = abs(weather_info["temperature"] - 15) * 50  # Ideal temp is 15°C
        humidity_penalty = weather_info["humidity"] * 100  # Strong penalty for high humidity
        wind_penalty = weather_info["wind_speed"] * 300  # Strong penalty for wind speed
        visibility_penalty = 3000 if weather_info["visibility"] < 5.0 else 0  # Harsh penalty for poor visibility
        precipitation_penalty = weather_info["precipitation"] * 1000  # Heavy penalty for rain
        total_cost += temp_penalty + humidity_penalty + wind_penalty + visibility_penalty + precipitation_penalty

    # Decrease the cost based on Aircraft's mach no (speed). Higher Speed = Low Cost
    total_cost -= aircraft_mach_no * 1000

    print(f"Route: {route}\nTotal Distance = {route_distance}kms\nAircraft Range = {aircraft_range}kms\nMach No = {aircraft_mach_no}\nTotal Cost: {total_cost}\n\n")
    return total_cost, route_distance

def fitness_function(population, cost_matrix, distance_matrix, iata_to_index, aircrafts_dict):
    fitness_values = []
    distances = []
    for route in population:
        # print(route)
        cost, distance = calculate_route_cost(route, cost_matrix, distance_matrix, iata_to_index, aircrafts_dict)
        if cost > 0:
            fitness = cost / 100
        else:
            fitness = float('inf')
        fitness_values.append(fitness)
        distances.append(distance)
    return fitness_values,distances