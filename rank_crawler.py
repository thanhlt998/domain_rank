from scrapy import Spider, Request, FormRequest
import json
import time
from lxml import etree
from twisted.internet import reactor, defer
from urllib.parse import urlencode
import datetime

from utils import get_domain_age_request_url, get_domain_popularity_request_url, get_url_with_scheme, get_ssl_info_url, \
    fix_url, get_domain
from mysql_connection import update_domain, update_ssl_grade, update_domain_age


class DomainRanking(Spider):
    def __init__(self, name=None, **kwargs):
        self.domain = kwargs.get('domain')
        self.sum_download_time = 0
        self.allowed_domains = [self.domain.domain_name, 'api.ssllabs.com', 'whois.inet.vn', 'data.alexa.com']
        self.ssl_grades = None
        self.out_domains = set()
        super(DomainRanking, self).__init__(name, **kwargs)

    def start_requests(self):
        self.crawler.stats.set_value("no_error_request", 0)
        self.crawler.stats.set_value("no_requests", 0)
        self.crawler.stats.set_value("no_new_posts", 0)

        start_requests = {
            "get_domain_age": {
                'request': Request,
                'params': {
                    "url": get_domain_age_request_url(domain=self.domain.domain_name),
                    "callback": self.get_domain_age_in_seconds
                }
            },
            # "get_ssl_grade": {
            #     "url": get_ssl_info_url(self.domain.domain_name, True),
            #     "callback": self.get_ssl_grade
            # },
            "get_domain_popularity": {
                'request': Request,
                'params': {
                    "url": get_domain_popularity_request_url(domain=self.domain.domain_name),
                    "callback": self.get_domain_popularity_alexa
                }
            },
            "get_error_rate": {
                'request': Request,
                'params': {
                    "url": get_url_with_scheme(domain=self.domain.domain_name),
                    "callback": self.get_error_rate,
                    "errback": self.check_error_back_rate
                }
            },
            "get_ssl_grade": {
                'request': FormRequest,
                'params': {
                    "url": "https://www.digicert.com/api/check-host.php",
                    "callback": self.get_ssl_info,
                    'method': 'POST',
                    'formdata': {
                        'r': '3',
                        'host': self.domain.domain_name,
                        'order_id': ''
                    }
                }

            }
        }

        for request in start_requests.values():
            yield request['request'](**request['params'])

    def parse(self, response):
        pass

    def get_domain_age_in_seconds(self, response):
        data = json.loads(response.text)
        creation_date = data.get('creationDate_L')
        if creation_date:
            self.domain.domain_age = time.time() - creation_date / 1000

    def get_domain_popularity_alexa(self, response):
        tree = etree.XML(response.body)
        popularity_text_nodes = tree.xpath("//ALEXA/SD/POPULARITY/@TEXT")
        if len(popularity_text_nodes) == 0:
            self.domain.domain_popularity = 0
        else:
            self.domain.domain_popularity = int(popularity_text_nodes[0])

    def get_error_rate(self, response):
        self.out_domains.add(get_domain(response.request.url))
        self.crawler.stats.inc_value("no_requests")
        if not self.domain.check_request_url(response.request.url):
            self.crawler.stats.inc_value('no_new_posts')
        self.sum_download_time += response.meta['request_time']
        urls = [response.urljoin(url.strip()) for url in response.xpath("//a/@href").getall() if fix_url(url)]
        for url in urls:
            yield Request(url=url, callback=self.get_error_rate, errback=self.check_error_back_rate)

    # def get_ssl_grade(self, response):
    #     ssl = json.loads(response.text)
    #     deferred = defer.Deferred()
    #
    #     if ssl['status'] != 'READY' and ssl['status'] != 'ERROR':
    #         reactor.callLater(30, deferred.callback, self.set_proxy(
    #             self.set_proxy(
    #                 Request(url=get_ssl_info_url(self.domain.domain_name, False), callback=self.get_ssl_grade))))
    #         return deferred
    #         # yield Request(url=get_ssl_info_url(self.domain.domain_name, False), callback=self.get_ssl_grade)
    #     else:
    #         self.ssl_grades = [endpoint.get('grade') for endpoint in ssl['endpoints'] if
    #                            endpoint.get('grade') is not None]
    #         print(self.ssl_grades)
    #         if len(self.ssl_grades) == 0:
    #             self.ssl_grades = ['FFF']

    def check_error_back_rate(self, failure):
        self.crawler.stats.inc_value("no_requests")
        self.crawler.stats.inc_value("no_error_request")

    def get_ssl_info(self, response):
        tree = etree.HTML(response.text)

        no_ok_test = len(tree.xpath("//h2[@class='ok']"))
        no_test = len(tree.xpath("//h2"))
        self.domain.ssl_grade = no_ok_test / no_test

    def close(self, spider, reason):
        no_error_requests = self.crawler.stats.get_value("no_error_request")
        no_new_requests = self.crawler.stats.get_value('no_requests')
        no_new_posts = self.crawler.stats.get_value("no_new_posts")
        self.domain.update_error_rate(no_new_requests, no_error_requests)
        self.domain.update_avg_request_time(no_new_requests, self.sum_download_time)
        self.domain.update_avg_new_posts_per_day(no_new_posts)
        self.domain.update_no_requested_requests(no_new_requests)

        self.logger.info(
            f"{self.domain.domain_name}, domain age: {self.domain.domain_age}, domain popularity: {self.domain.domain_popularity}, "
            f"error rate: {self.domain.error_rate}, avg request time:{self.domain.avg_request_time}, no new posts: {no_new_posts}, "
            f"avg new posts per day: {self.domain.avg_new_posts_per_day}, ssl grade: {self.domain.ssl_grade}")

        update_domain(domain=self.domain, out_domains=self.out_domains)
        print(f"updated domain {self.domain.domain_name} in database")

    @staticmethod
    def set_proxy(request):
        request.meta['proxy'] = f"http://171.255.192.118:8080"
        return request


class SSLCrawler(Spider):
    custom_settings = {
        'DOWNLOAD_DELAY': 5,
    }

    def __init__(self, name=None, **kwargs):
        self.domains = kwargs.get("domains")
        self.result = {}
        self.no_assessment = 0
        super(SSLCrawler, self).__init__(name, **kwargs)

    def start_requests(self):
        for domain in self.domains:
            yield Request(url=get_ssl_info_url(domain, False), callback=self.parse, meta={'domain': domain})

    def parse(self, response):
        domain = response.meta['domain']
        ssl = json.loads(response.text)

        if ssl['status'] != 'READY' and ssl['status'] != 'ERROR':
            deferred = defer.Deferred()
            reactor.callLater(40, deferred.callback,
                              Request(url=get_ssl_info_url(domain, False), callback=self.parse, meta={'domain': domain},
                                      dont_filter=True))
            return deferred

        else:
            if ssl['status'] == 'READY':
                ssl_grades = [endpoint.get('grade') for endpoint in ssl['endpoints'] if
                              endpoint.get('grade') is not None]
                if len(ssl_grades) == 0:
                    ssl_grades = ['F']
            else:
                ssl_grades = ['F']

            self.result[domain] = ''.join(ssl_grades)

    def close(self, spider, reason):
        print('ssl', self.result)
        update_ssl_grade(self.result)


class ParsingDomain(Spider):
    name = 'parsing_domain'
    custom_settings = {
        'DOWNLOAD_DELAY': 0.1,
        'FEED_EXPORT': 'jsonlines',
        'FEED_URI': 'parsing_domain_data.jsonl',
        'FEED_EXPORT_ENCODING': 'utf-8'
    }

    def __init__(self, name=None, **kwargs):
        self.domains = kwargs.get("domains")
        super(ParsingDomain, self).__init__(name, **kwargs)

    def start_requests(self):
        print(len(self.domains))
        for domain in self.domains:
            yield Request(url="http://192.168.1.240:8089/tagger/v1/character", method="POST",
                          headers={'Content-Type': 'application/json',
                                   'Authorization': "Basic YWRmaWxleDphZGZpbGV4QDIwMTk="},
                          body=f'{{"text": "{domain.domain_name}"}}',
                          callback=self.parse,
                          meta={'domain': domain.domain_name},
                          dont_filter=True)

    def parse(self, response):
        data = json.loads(response.text)
        yield {'domain': response.meta['domain'], **data}


class DomainAgeCrawler(Spider):
    name = 'age_crawler'

    custom_settings = {
        'DOWNLOAD_DELAY': 0.1
    }

    def __init__(self, name=None, **kwargs):
        self.domains = kwargs.get("domains")
        self.domain_ages = []
        super(DomainAgeCrawler, self).__init__(name, **kwargs)

    def start_requests(self):
        for domain in self.domains:
            yield Request(url=get_domain_age_request_url(domain.domain_name), callback=self.parse,
                          meta={'domain_id': domain.domain_id})

    def parse(self, response):
        domain_id = response.meta['domain_id']
        data = json.loads(response.text)
        creation_date = data.get('creationDate_L')
        if creation_date:
            domain_age = time.time() - creation_date / 1000
        else:
            domain_age = 0

        self.domain_ages.append((domain_id, domain_age))

    def close(self, spider, reason):
        update_domain_age(self.domain_ages)
