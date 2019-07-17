from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from scrapy.utils.log import configure_logging

from rank_crawler import DomainRanking, ParsingDomain, DomainAgeCrawler
from settings import SETTINGS
from mysql_connection import select_domain_objects, select_crawled_urls, select_not_crawled_domains
from settings import NO_MAX_CONCURRENT_SPIDER
from pagerank import calculate_pagerank
from ahp import calculate_score


def crawl():
    i = 0
    while i < NO_MAX_CONCURRENT_SPIDER:
        if len(domains) > 0:
            domain = domains.pop()
            domain.requested_urls = select_crawled_urls(domain.domain_id)
            deffered = process.crawl(DomainRanking, name=domain.domain_name, domain=domain)
            deffered.addCallback(start_new_spider)
            i += 1
        else:
            break


def start_new_spider(result):
    if len(domains) > 0:
        domain = domains.pop()
        deffered = process.crawl(DomainRanking, name=domain.domain_name, domain=domain)
        deffered.addCallback(start_new_spider)


def crawl_domain_age():
    process.crawl(DomainAgeCrawler, name="domain_age_crawler", domains=domains)


if __name__ == '__main__':
    s = get_project_settings()
    s.update(SETTINGS)
    process = CrawlerProcess(s)

    configure_logging()
    # domains = select_not_crawled_domains()
    domains = select_domain_objects(start_id=1, end_id=20, contain_crawled_urls=False)
    domains.reverse()
    print("Start crawling")
    crawl()
    # crawl_domain_age()
    process.start()

    print("Start calculating pagerank")
    calculate_pagerank()

    print("Start calculating score")
    calculate_score()
