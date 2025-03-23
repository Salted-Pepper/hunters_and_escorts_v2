import constants as cs
from perlin_noise import PerlinNoise


def update_sea_states(grid) -> None:
    """
    Creates sampled probabilities based on Perlin Noise.
    Once the cumulative transition probability exceeds this random value, sets it to the corresponding state.
    :param grid:
    :return:
    """
    update_u_values(grid)

    for receptor in grid.receptors:
        transition_probabilities = cs.weather_markov_dict[receptor.sea_state]
        prob = 0
        for key in transition_probabilities.keys():
            prob += transition_probabilities[key]
            if prob > receptor.new_uniform_value:
                receptor.sea_state = key
                break


def update_u_values(grid) -> None:
    """
    Updates the uniform probabilities for each receptor, which serves as input to sample the next transition
    in the Markov Chain.
    :param grid:
    :return:
    """
    cols = grid.max_cols
    rows = grid.max_rows

    noise = PerlinNoise(octaves=8)
    noise_data = [[noise([j / rows, i / cols]) for i in range(cols)] for j in range(rows)]
    # normalize noise
    min_value = min(x if isinstance(x, int) else min(x) for x in noise_data)
    noise_data = [[n + abs(min_value) for n in rows] for rows in noise_data]
    max_value = max(x if isinstance(x, int) else max(x) for x in noise_data)
    noise_data = [[n / max_value for n in rows] for rows in noise_data]
    min(x if isinstance(x, int) else min(x) for x in noise_data)
    max(x if isinstance(x, int) else max(x) for x in noise_data)
    new_u_matrix = noise_data

    for index, receptor in enumerate(grid.receptors):
        receptor.last_uniform_value = receptor.new_uniform_value
        receptor.new_uniform_value = new_u_matrix[index // cols][index % cols]
