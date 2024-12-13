import numpy as np
import pandas as pd
import json
import random
from fitness_function import fitness_function
from GA_utils import initialize_population, tournament_selection, crossover, swap_mutation
from preprocessing import create_routes_dictionary, create_cost_distance_matrix, create_aircrafts_dictionary

def genetic_algorithm(source, destination, cost_matrix, distance_matrix, airports, aircrafts_dict, iata_to_index, population_size=10, generations=3, tournament_size=5, mutation_rate=0.1):
    population = initialize_population(source, destination, airports, aircrafts_dict, population_size)

    best_route = None
    best_fitness = float('inf')
    best_distance = 0

    for generation in range(generations):
        fitness_values, distances = fitness_function(population, cost_matrix, distance_matrix, iata_to_index, aircrafts_dict)

        current_best_route_index = fitness_values.index(min(fitness_values))
        current_best_route = population[current_best_route_index]
        current_best_route_fitness = fitness_values[current_best_route_index]
        
        if current_best_route_fitness < best_fitness:
            best_fitness = current_best_route_fitness
            best_route = current_best_route
            best_distance=distances[current_best_route_index]

        new_population = [current_best_route]

        while len(new_population) < population_size:
            parent1, parent2 = tournament_selection(population, fitness_values, tournament_size)
            
            # Crossover
            if random.random() < 0.8:
                child1, child2 = crossover(parent1, parent2)
            else:
                child1, child2 = parent1[:], parent2[:]

            # Mutation
            child1 = swap_mutation(child1, mutation_rate)
            child2 = swap_mutation(child2, mutation_rate)

            new_population.extend([child1, child2])

        population = new_population[:population_size]

    return {'best_route': best_route, 'total_cost': best_fitness, 'total_distance':best_distance}

def optimize_route(source, destination, aircraft_model, date, list_of_aircrafts):
    try:
        # Load necessary data
        with open('airline_routes.json', 'r') as file:
            airline_routes = json.load(file)

        aircrafts = pd.read_csv("Aircrafts.csv")
        aircrafts_dict = create_aircrafts_dictionary(aircrafts, list_of_aircrafts)

        routes_info_dict = create_routes_dictionary(airline_routes)
        airports = list(routes_info_dict.keys())
        iata_to_index = {iata: idx for idx, iata in enumerate(airports)}

        cost_matrix, distance_matrix = create_cost_distance_matrix(routes_info_dict, airports, airline_routes)

        # Call the genetic algorithm
        result = genetic_algorithm(
            source=source,
            destination=destination,
            cost_matrix=cost_matrix,
            distance_matrix=distance_matrix,
            airports=airports,
            aircrafts_dict=aircrafts_dict,
            iata_to_index=iata_to_index
        )


        return result

    except Exception as e:
        raise RuntimeError(f"Optimization failed: {e}")
