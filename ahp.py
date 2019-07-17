import numpy as np
from mysql_connection import select_domains, update_score
import time

from settings import CRITERIA_WEIGHT, CRITERIA_TYPE, CRITERIA_LIST, COMPARISON_MATRIX, CRITERIA_INDEX, RI


def get_criteria_matrix():
    map_index = {}
    for i, criteria in enumerate(CRITERIA_TYPE.keys()):
        map_index[i] = CRITERIA_INDEX[criteria]

    n = len(map_index)
    matrix = np.ones((n, n))

    for i in range(n):
        for j in range(n):
            matrix[i, j] = COMPARISON_MATRIX[map_index[i]][map_index[j]]

    return matrix


def sigmoid(x):
    return 1 / (1 + np.exp(-x))


def normalize(values):
    min_value = values.min()
    max_value = values.max()

    def norm(x):
        return 2 * (x - min_value) / (max_value - min_value) - 1

    return norm(values)


def check_criteria_comparison_matrix(matrix, eps=0.1):
    w, v = np.linalg.eig(matrix)
    n = matrix.shape[0]

    max_eigenvalue = w.max()
    ci = (max_eigenvalue - n) / (n - 1)
    cr = ci / RI[n - 1]
    print(f"max eigenvalue: {max_eigenvalue}, cr: {cr}")
    return cr < eps


def get_alternative_matrix(criteria, domains, type='benefit'):
    dimension = len(domains)
    matrix = np.ones((dimension, dimension), dtype=np.float64)
    criteria_values = np.array([domain[criteria] for domain in domains])
    # criteria_values /= np.linalg.norm(criteria_values)
    criteria_values = normalize(criteria_values)
    normalized_values = [sigmoid(criteria_value) for criteria_value in criteria_values]

    # sigmoid_values = [sigmoid(domain[criteria]) for domain in domains]

    for i in range(dimension):
        for j in range(i + 1, dimension):
            w_i = normalized_values[i]
            w_j = normalized_values[j]

            if type == 'benefit':
                matrix[i, j] = w_i / w_j
                matrix[j, i] = w_j / w_i
            else:
                matrix[i, j] = w_j / w_i
                matrix[j, i] = w_i / w_j

    return matrix


def get_weight_from_matrix(matrix):
    mean_array = np.mean(matrix, axis=1)
    sum = np.sum(mean_array)
    norm_array = mean_array / sum
    return norm_array


def calculate_score():
    domains = select_domains(contain_crawled_urls=False)

    matrices = {}
    weight_critetia_alternatives = {}

    for criteria, type in CRITERIA_TYPE.items():
        matrices[criteria] = get_alternative_matrix(criteria, domains, type)

    for criteria, matrix in matrices.items():
        weight_critetia_alternatives[criteria] = get_weight_from_matrix(matrix)

    weight_critetia_alternatives_matrix = np.array(
        [weight for weight in weight_critetia_alternatives.values()]).T

    criteria_weights = get_weight_from_matrix(get_criteria_matrix()).reshape(-1, 1)

    result = weight_critetia_alternatives_matrix.dot(criteria_weights).reshape(1, -1)[0]

    with open('ahp_result.txt', mode='w', encoding='utf8') as f:
        for i, score in enumerate(result):
            f.write(f"{domains[i]['domain_name']}\t{score}\n")
        f.close()

    update_score([(domains[i]['domain_id'], score) for i, score in enumerate(result)])


if __name__ == '__main__':
    print(time.asctime())
    calculate_score()
    print(time.asctime())
    # print(check_criteria_comparison_matrix(np.array(COMPARISON_MATRIX)))
    # print(get_criteria_matrix())
