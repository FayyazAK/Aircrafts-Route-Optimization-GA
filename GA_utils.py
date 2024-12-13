import random, copy

def generate_route(source_iata, destination_iata, airports, aircrafts_dict):
    available_airports = [a for a in airports if a not in [source_iata, destination_iata]]

    num_intermediate = random.randint(0, min(10, len(available_airports)))

    intermediate_stops = random.sample(available_airports, num_intermediate)

    aircraft = random.sample(list(aircrafts_dict.keys()), 1)

    route = [aircraft] + [source_iata] + intermediate_stops + [destination_iata]
    return route


def initialize_population(source_iata, destination_iata, airports, aircrafts_dict, pop_size):
    population = []
    for _ in range(pop_size):
        route = generate_route(source_iata, destination_iata, airports, aircrafts_dict)
        if route not in population:
            population.append(route)
        # print("Pop --> ", route)
    return population


def tournament_selection(population, fitness_values, tournament_size):
    print("Length of pop: ",len(population))
    if len(population) < tournament_size:
        return population[0], population[1]
    selected_indices = random.sample(range(len(population)), tournament_size)
    selected_routes = [population[i] for i in selected_indices]
    selected_fitness = [fitness_values[i] for i in selected_indices]
    
    # Sort routes by fitness values
    sorted_pairs = sorted(zip(selected_fitness, selected_routes), key=lambda x: x[0])
    best_two_routes = [route for _, route in sorted_pairs[:2]]
    
    # print(f"* In Tournament selection, best two routes: {best_two_routes} \n")
    return best_two_routes[0], best_two_routes[1]

def crossover(parent1, parent2):
    print("\n***** In Cross Over Function *****\n")
    parent1_aircraft = parent1[0]
    parent2_aircraft = parent2[0]
    # parent1 = parent1[1:]
    # parent2 = parent2[1:]
    origin = parent1[1]
    destination = parent1[-1]

    parent1 = copy.deepcopy(parent1[2:-1])
    parent2 = copy.deepcopy(parent2[2:-1])
    print(f"Parents for crossover \nParent 1 {parent1}\nPrent2 {parent2}")
    print(f"The origin is {origin} and destination is {destination}")

    if ( min( len(parent1), len(parent2) ) ) != 0:
        crossover_point = random.randint(1, min( len(parent1), len(parent2) ))
        child1 = parent1 + parent2[crossover_point:]
        child2 = parent2 + parent1[crossover_point:]
        child1 = [origin] + child1 + [destination]
        child2 = [origin] + child2 + [destination]
        if random.random() < 0.5: #There is a 50% chance of Aircrafts crossover.
            child1 = [parent2_aircraft] + child1
            child2 = [parent1_aircraft] + child2
        else:
            child1 = [parent1_aircraft] + child1
            child2 = [parent2_aircraft] + child2
        return child1, child2
    else: #if it is a direct route (no intermediate cities) then only crossover the aircrafts.
        child1 = [city for city in parent1]
        child2 = [city for city in parent2]
        child1 = [parent2_aircraft] + [origin] + child1 + [destination]
        child2 = [parent1_aircraft] + [origin] + child2 + [destination]
        return child1, child2

def swap_mutation(route, mutation_rate = 0.1):
    print(f"Route for mutation {route}")
    aircraft = route[0]
    origin = route[1]
    destination = route[-1]
    route = copy.deepcopy(route[2:-1])
    # print(f"Route for mutation after proc {route}")
    if len(route) != 0:
        for i in range(len(route)):
            if random.random() < mutation_rate:
                j = random.randint(0, len(route) - 1)
                route[i], route[j] = route[j], route[i]
        route = [aircraft] + [origin] + route + [destination]
    else:
        route = [aircraft] + [origin] + [destination]
    return route