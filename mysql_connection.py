import pymysql
import pymysql.cursors as cursors
import os
import json
import time
import datetime

from domain_class import Domain
from settings import DB


def get_connection(host, user, password, db):
    try:
        connection = pymysql.connect(host=host, user=user, password=password, db=db, charset="utf8",
                                     cursorclass=cursors.DictCursor)
        return connection
    except Exception:
        print("Can't connect to the database")
        return None


def init_database():
    connection = get_connection(DB['host'], DB['user'], DB['password'], DB['db'])
    domains = get_domain_list('domain_crawled_urls')

    insert_domains(connection, domains)
    insert_urls(connection, domains)
    insert_domain_to_domain(connection)


def insert_domains(connection, domains):
    sql = 'insert into domain (domain_id, domain_name, first_time_crawl, last_time_updated, domain_age, domain_popularity, ' \
          'error_rate, avg_request_time, avg_new_posts_per_day, no_requested_requests, ssl_grade, no_sub_domains, domain_length) values ' \
          '(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'

    with connection.cursor() as cursor:
        cursor.executemany(sql, [
            domain.get_info() for domain in domains
        ])

    connection.commit()


def insert_domain_to_domain(connection):
    domain_id_domain_name_sql = "select domain_id, domain_name from domain"
    insert_domain_to_domain_sql = "insert into domain_to_domain values (%s, %s)"
    update_no_out_domains_sql = "update domain set no_out_domains = %s where domain_id = %s"
    with connection.cursor() as cursor:
        cursor.execute(domain_id_domain_name_sql)
        domain_indices = {domain['domain_name']: domain['domain_id'] for domain in cursor.fetchall()}

        with open('processed_data/domain_out_domains.jsonl', mode='r') as f:
            for line in f:
                obj = json.loads(line)
                domain_id = domain_indices[obj['domain']]
                out_domain_ids = [domain_indices[out_domain] for out_domain in obj['out_domains'] if
                                  domain_indices.get(out_domain) is not None]
                cursor.executemany(insert_domain_to_domain_sql, [
                    (domain_id, out_domain_id) for out_domain_id in out_domain_ids
                ])
                cursor.execute(update_no_out_domains_sql, (len(obj['out_domains']), domain_id))
            f.close()
        connection.commit()


def insert_urls(connection, domains):
    timestamp = '{0:%Y-%m-%d %H:%M:%S}'.format(datetime.datetime.fromtimestamp(1562729443.8829284))
    sql = 'insert into crawled_urls (domain_id, url, time_crawled) values (%s, %s, %s)'
    domain_urls = []
    for domain in domains:
        for url in domain.requested_urls:
            domain_urls.append((domain.domain_id, url, timestamp))

    with connection.cursor() as cursor:
        cursor.executemany(sql, domain_urls)

    connection.commit()


def get_domain_list(data_folder):
    domains = []
    i = 1
    for file_name in os.listdir(data_folder):
        with open(f"{data_folder}/{file_name}", mode='r', encoding='utf8') as f:
            category = json.load(f)
            for domain_name, urls in category.items():
                domains.append(Domain(domain_name=domain_name,
                                      first_time_crawl=time.time(),
                                      last_time_updated=time.time(),
                                      domain_age=0,
                                      requested_urls=urls,
                                      no_requested_requests=len(urls),
                                      domain_id=i,
                                      no_sub_domains=domain_name.count('.') - 1,
                                      domain_length=len(domain_name),
                                      ))
                i += 1

    return domains


def update_domain(domain, out_domains=None):
    connection = get_connection(DB['host'], DB['user'], DB['password'], DB['db'])
    update_domain_sql = "update domain set " \
                        "last_time_updated = %s, " \
                        "domain_age = %s, " \
                        "domain_popularity = %s, " \
                        "error_rate = %s, " \
                        "avg_request_time = %s, " \
                        "avg_new_posts_per_day = %s, " \
                        "no_requested_requests = %s, " \
                        "ssl_grade = %s " \
                        "where domain_id = %s"

    with connection.cursor() as cursor:
        cursor.execute(update_domain_sql,
                       (domain.last_time_updated, domain.domain_age, domain.domain_popularity, domain.error_rate,
                        domain.avg_request_time, domain.avg_new_posts_per_day, domain.no_requested_requests,
                        domain.ssl_grade, domain.domain_id))

    if len(domain.new_request_urls) > 0:
        update_urls_sql = "insert into crawled_urls (domain_id, url, time_crawled) values (%s, %s, %s)"
        with connection.cursor() as cursor:
            cursor.executemany(update_urls_sql, [
                (domain.domain_id, url, time_crawled) for url, time_crawled in domain.new_request_urls
            ])

    connection.commit()

    with connection.cursor() as cursor:
        if out_domains and len(out_domains) > 0:
            select_domain_ids_sql = f"select domain_id from domain " \
                f"where domain_name in ({', '.join(['%s'] * len(out_domains))}) " \
                f"and domain_id not in " \
                f"(select to_domain_id from domain_to_domain where from_domain_id = %s)"
            cursor.execute(select_domain_ids_sql, (*out_domains, domain.domain_id))
            new_out_domain_ids = [obj['domain_id'] for obj in cursor.fetchall()]

            update_out_domains_sql = "insert domain_to_domain (from_domain_id, to_domain_id) values (%s, %s)"
            cursor.executemany(update_out_domains_sql, [
                (domain.domain_id, out_domain_id) for out_domain_id in new_out_domain_ids
            ])

            update_no_out_domains = "update domain set no_out_domains = no_out_domains + %s where domain_id = %s"
            cursor.execute(update_no_out_domains, (len(out_domains), domain.domain_id))
    connection.commit()

    connection.close()


def select_domain_objects(start_id=None, end_id=None, contain_crawled_urls=True):
    domains = select_domains(start_id, end_id, contain_crawled_urls)

    result = []
    for domain in domains:
        result.append(Domain(**domain))
    return result


def select_domains(start_id=None, end_id=None, contain_crawled_urls=True):
    connection = get_connection(DB['host'], DB['user'], DB['password'], DB['db'])
    select_domain_sql = "select * from domain where domain_id between %s and %s"
    select_all_domain_sql = "select * from domain"
    select_out_domains = "select domain_name from domain where domain_id in (" \
                         "select to_domain_id from domain_to_domain where from_domain_id = %" \
                         ")"
    result = []

    with connection.cursor() as cursor:
        if start_id and end_id:
            cursor.execute(select_domain_sql, (start_id, end_id))
        else:
            cursor.execute(select_all_domain_sql)
        domains = cursor.fetchall()

        if contain_crawled_urls:
            select_urls_sql = "select url from crawled_urls where domain_id = %s"

            for domain in domains:
                cursor.execute(select_urls_sql, (domain['domain_id'],))
                domain['requested_urls'] = [url['url'] for url in cursor.fetchall()]
                result.append(domain)
        else:
            for domain in domains:
                domain['requested_urls'] = []
                result.append(domain)

    connection.close()
    return result


def select_not_crawled_domains():
    connection = get_connection(DB['host'], DB['user'], DB['password'], DB['db'])
    select_domain_sql = "select * from domain where domain_age = 0" \
                        # " and domain_popularity = 0" \
                        # " and error_rate=0" \
                        # " and avg_request_time = 0" \
                        # " and avg_new_posts_per_day = 0"
    result = []

    with connection.cursor() as cursor:
        cursor.execute(select_domain_sql)
        domains = cursor.fetchall()

        for domain in domains:
            domain['requested_urls'] = []
            result.append(Domain(**domain))

    connection.close()
    return result


def select_crawled_urls(domain_id):
    connection = get_connection(DB['host'], DB['user'], DB['password'], DB['db'])
    select_urls_sql = "select url from crawled_urls where domain_id = %s"
    with connection.cursor() as cursor:
        cursor.execute(select_urls_sql, domain_id)

    result = [url['url'] for url in cursor.fetchall()]
    connection.close()
    return result


def update_ssl_grade(domain_grade):
    connection = get_connection(DB['host'], DB['user'], DB['password'], DB['db'])
    update_ssl_sql = "update domain set ssl_grade = %s where domain_name = %s"

    with connection.cursor() as cursor:
        cursor.executemany(update_ssl_sql, [
            (ssl_grade, domain_name) for domain_name, ssl_grade in domain_grade.items()
        ])
    connection.commit()
    connection.close()


def insert_url_outlinks():
    pass


def update_score(domain_id_score):
    connection = get_connection(DB['host'], DB['user'], DB['password'], DB['db'])
    sql = "update domain set score = %s where domain_id = %s"
    with connection.cursor() as cursor:
        cursor.executemany(sql, [
            (float(score), domain_id) for domain_id, score in domain_id_score
        ])
    connection.commit()
    connection.close()


def update_meaning_word_rate(domain_meaning_word_rate):
    connection = get_connection(DB['host'], DB['user'], DB['password'], DB['db'])
    sql = 'update domain set meaning_word_rate = %s where domain_name like %s'

    with connection.cursor() as cursor:
        cursor.executemany(sql, [
            (meaning_word_rate, domain_name) for domain_name, meaning_word_rate in domain_meaning_word_rate
        ])
    connection.commit()
    connection.close()


def update_domain_age(domain_id_domain_age):
    connection = get_connection(DB['host'], DB['user'], DB['password'], DB['db'])
    sql = 'update domain set domain_age = %s where domain_id = %s'

    with connection.cursor() as cursor:
        cursor.executemany(sql, [
            (domain_age, domain_id) for domain_id, domain_age in domain_id_domain_age
        ])
    connection.commit()
    connection.close()


if __name__ == '__main__':
    # connection = get_connection(DB['host, DB['user, DB['password, DB['db)
    init_database()
    # select_domains()
