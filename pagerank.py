import numpy as np
from scipy.sparse import coo_matrix
import json

from mysql_connection import get_connection
from settings import DB


def page_rank(M, eps=1.0e-8, d=0.85):
    N = M.shape[1]
    v = np.random.rand(N, 1)
    v = v / np.linalg.norm(v, 1)
    last_v = np.ones((N, 1), dtype=np.float32) * 100

    while np.linalg.norm(v - last_v, 2) > eps:
        last_v = v
        v = d * (M.dot(v)) + (1 - d) / N
    return v


def get_matrix():
    row_indices = []
    col_indices = []
    values = []

    urls = {}
    with open('url_no_outlinks_income_links.jsonl', mode='r') as f:
        for line in f:
            obj = json.loads(line)
            urls[obj['index']] = obj
        f.close()

    no_urls = len(urls)

    for index, obj in urls.items():
        if not obj.get('income_links_index'):
            continue
        for income_link_index in obj['income_links_index']:
            if index == income_link_index:
                continue
            row_indices.append(index)
            col_indices.append(income_link_index)

            no_outlinks = urls[income_link_index]['no_outlinks']

            values.append(1 / no_outlinks if no_outlinks != 0 else 1 / no_urls)

    del urls

    return coo_matrix((np.array(values), (np.array(row_indices), np.array(col_indices))), shape=(no_urls, no_urls),
                      dtype=np.float32)


def get_domain_matrix():
    index_domain = {}
    with open("domain_out_domains.jsonl", mode='r') as f:
        domains = {}
        i = 0
        for line in f:
            obj = json.loads(line)
            obj['index'] = i
            domains[obj['domain']] = obj
            index_domain[i] = obj['domain']
            i += 1
        f.close()

    no_domains = len(domains)

    for domain_name, domain in domains.items():
        domain['no_out_domains'] = len(domain['out_domains'])
        for out_domain in domain['out_domains']:
            obj = domains.get(out_domain)
            if obj:
                income_domain_indices = obj.setdefault("income_domain_indices", [])
                income_domain_indices.append(domain['index'])

    row_indices = []
    col_indices = []
    values = []

    for domain_name, domain in domains.items():
        if domain.get('income_domain_indices'):
            for income_domain_index in domain['income_domain_indices']:
                row_indices.append(domain['index'])
                col_indices.append(income_domain_index)
                no_out_domains = domains[index_domain[income_domain_index]]['no_out_domains']
                values.append(1 / no_out_domains if no_out_domains != 0 else 1 / no_domains)

    # print(row_indices)
    return coo_matrix((values, (row_indices, col_indices)), shape=(no_domains, no_domains),
                      dtype=np.float32), index_domain


def get_maxtrix_from_db():
    connection = get_connection(DB['host'], DB['user'], DB['password'], DB['db'])
    domain_id_no_out_domains_sql = "select domain_id, no_out_domains from domain"
    from_domain_to_domain_sql = "select * from domain_to_domain"

    row_indices = []
    col_indices = []
    values = []

    with connection.cursor() as cursor:
        cursor.execute(domain_id_no_out_domains_sql)
        domain_id_no_out_domains = {obj['domain_id']: obj['no_out_domains'] for obj in cursor.fetchall()}
        cursor.execute(from_domain_to_domain_sql)
        from_domain_to_domain = cursor.fetchall()

        no_domains = len(domain_id_no_out_domains)

        for obj in from_domain_to_domain:
            row_indices.append(obj['to_domain_id'])
            col_indices.append(obj['from_domain_id'])
            values.append(1 / domain_id_no_out_domains[obj['from_domain_id']]
                          if domain_id_no_out_domains[obj['from_domain_id']] != 0 else 1 / no_domains)

    return coo_matrix((np.array(values), (np.array(row_indices) - 1, np.array(col_indices) - 1)),
                      shape=(no_domains, no_domains),
                      dtype=np.float32)


def test():
    M, index_domain = get_domain_matrix()
    v = page_rank(M, 0.001, 0.85).reshape((1, -1))[0]

    domain_rank = [(index_domain[i], v) for i, v in enumerate(v)]
    domain_rank = sorted(domain_rank, key=lambda x: x[1])
    with open("domain_rank_result.txt", mode='w') as f:
        for domain, rank in domain_rank:
            f.write(f"{domain}: {rank}\n")

        f.close()


def calculate_pagerank():
    M = get_maxtrix_from_db()
    v = page_rank(M, 0.001, 0.85).reshape((1, -1))[0]

    # with open('rank_result_from_db.txt', mode='w') as f:
    #     for i, rank in enumerate(v):
    #         f.write(f"{i}\t{rank}\n")
    #     f.close()

    connection = get_connection(DB['host'], DB['user'], DB['password'], DB['db'])
    update_pagerank_sql = "update domain set pagerank = %s where domain_id = %s"

    with connection.cursor() as cursor:
        cursor.executemany(update_pagerank_sql, [
            (float(rank), i + 1) for i, rank in enumerate(v)
        ])
        connection.commit()
    connection.close()


if __name__ == '__main__':
    calculate_pagerank()
