import time
from datetime import timedelta
import datetime
from bloom_filter import BloomFilter


class Domain:
    def __init__(self, domain_name, first_time_crawl, last_time_updated, domain_age, requested_urls=[],
                 domain_popularity=0,
                 no_requested_requests=0,
                 error_rate=0,
                 avg_request_time=0,
                 avg_new_posts_per_day=0,
                 domain_id=0,
                 no_out_domains=0,
                 pagerank=0,
                 ssl_grade=0,
                 meaning_word_rate=0,
                 no_sub_domains=0,
                 domain_length=0,
                 score=0):
        self.domain_name = domain_name
        self.first_time_crawl = 1562729024.9279761
        self.last_time_updated = 1562729443.8829284
        self.domain_age = domain_age
        self.requested_urls = requested_urls
        self.domain_popularity = domain_popularity
        self.no_requested_requests = no_requested_requests
        self.error_rate = error_rate
        self.avg_request_time = avg_request_time
        self.avg_new_posts_per_day = avg_new_posts_per_day
        self.ssl_grade = ssl_grade
        self.domain_id = domain_id
        self.meaning_word_rate = meaning_word_rate
        self.no_sub_domains = no_sub_domains
        self.domain_length = domain_length
        self.score = score

        self.new_request_urls = []
        self.urls_bloom_filter = self.get_urls_bloom_filter(requested_urls)

    def update_error_rate(self, no_new_requests, no_new_error_requests):
        self.error_rate = (self.error_rate * self.no_requested_requests + no_new_error_requests) / (
                self.no_requested_requests + no_new_requests)

    def update_avg_request_time(self, no_new_requests, sum_request_time):
        self.avg_request_time = (self.avg_request_time * self.no_requested_requests + sum_request_time) / (
                self.no_requested_requests + no_new_requests)

    def update_domain_age(self, domain_age):
        self.domain_age = domain_age

    def update_domain_popularity(self, domain_popularity):
        self.domain_popularity = domain_popularity

    def update_time_crawl(self, now):
        self.last_time_updated = now

    def update_no_requested_requests(self, no_new_requests):
        self.no_requested_requests += no_new_requests

    def is_requested_url(self, url):
        return url in self.urls_bloom_filter

    def update_avg_new_posts_per_day(self, no_new_posts):
        now = time.time()
        first_time_to_last_updated = self.get_time_interval_in_day(self.first_time_crawl, self.last_time_updated)
        first_time_to_now = self.get_time_interval_in_day(self.last_time_updated, now)
        self.avg_new_posts_per_day = (
                                             self.avg_new_posts_per_day * first_time_to_last_updated + no_new_posts) / first_time_to_now
        self.update_time_crawl(now)

    def update_ssl_grade(self, ssl_grade):
        self.ssl_grade = ssl_grade

    def check_request_url(self, url):
        is_requested = self.is_requested_url(url)
        if not is_requested:
            self.new_request_urls.append((url, '{0:%Y-%m-%d %H:%M:%S}'.format(datetime.datetime.now())))

        return is_requested

    def get_info(self):
        return (self.domain_id, self.domain_name, self.first_time_crawl, self.last_time_updated, self.domain_age,
                self.domain_popularity, self.error_rate, self.avg_request_time, self.avg_new_posts_per_day,
                self.no_requested_requests, self.ssl_grade, self.no_sub_domains, self.domain_length)

    @staticmethod
    def get_urls_bloom_filter(urls):
        bloom_filter = BloomFilter(max_elements=10000, error_rate=0.001)
        for url in urls:
            bloom_filter.add(url)

        return bloom_filter

    @staticmethod
    def get_time_interval_in_day(start_time, end_time):
        interval = timedelta(seconds=end_time - start_time)
        return interval.days if interval.seconds == 0 else interval.days + 1

    def __str__(self):
        return f"domain_id: {self.domain_id}, domain_name: {self.domain_name}, first_time_crawl: {self.first_time_crawl}, " \
            f"last_time_updated: {self.last_time_updated}, domain_age: {self.domain_age}, " \
            f"domain_popularity: {self.domain_popularity}, error_rate: {self.error_rate}, " \
            f"avg_request_time: {self.avg_request_time}, avg_new_posts_per_day: {self.avg_new_posts_per_day}"
