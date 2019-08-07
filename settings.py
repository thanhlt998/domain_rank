DB = {
    'host': 'localhost',
    'user': 'root',
    'password': '123456',
    'db': 'domain_rank'
}

NO_MAX_CONCURRENT_SPIDER = 100

SETTINGS = {
    'DEPTH_LIMIT': 1,
    'LOG_FILE': 'file.log',

    'DOWNLOADER_MIDDLEWARES': {
        'middlewares.TimeDownloaderMiddleware': 1,
        'scrapy.contrib.downloadermiddleware.useragent.UserAgentMiddleware': None,
        'random_useragent.RandomUserAgentMiddleware': 10,
    },

    'DUPEFILTER_CLASS': 'filters.BLOOMDupeFilter',

    'DEPTH_PRIORITY': 1,
    'DOWNLOAD_DELAY': 1,
    'CONCURRENT_REQUESTS': 1,
    'CONCURRENT_REQUESTS_PER_DOMAIN': 1,
    'LOG_LEVEL': 'INFO',
    'COOKIES_ENABLED': False,
    'TELNETCONSOLE_PORT': None,

    'USER_AGENT_LIST': 'user_agent.txt',

    'CLOSESPIDER_TIMEOUT': 3600  # 1 hours
}

# AHP settings
CRITERIA_LIST = ['domain_age',
                 'domain_popularity',
                 'error_rate',
                 'avg_request_time',
                 'avg_new_posts_per_day',
                 'pagerank',
                 'ssl_grade',
                 'meaning_word_rate',
                 'no_sub_domains',
                 'domain_length'
                 ]
CRITERIA_TYPE = {
    'domain_age': 'benefit',
    'domain_popularity': 'cost',
    'error_rate': 'cost',
    'avg_request_time': 'cost',
    'avg_new_posts_per_day': 'benefit',
    'pagerank': 'benefit',
    'ssl_grade': 'benefit',
    'meaning_word_rate': 'benefit',
    'no_sub_domains': 'cost',
    'domain_length': 'cost'
}

# Critetia comparison matrix
CRITERIA_INDEX = {
    'domain_age': 0,
    'domain_popularity': 1,
    'error_rate': 2,
    'avg_request_time': 3,
    'avg_new_posts_per_day': 4,
    'pagerank': 5,
    'ssl_grade': 6,
    'meaning_word_rate': 7,
    'no_sub_domains': 8,
    'domain_length': 9
}

COMPARISON_MATRIX = [
    [1, 1 / 4, 1 / 3, 1 / 2, 1 / 7, 1 / 5, 1, 1 / 3, 1, 2],
    [4, 1, 5, 5, 1, 2, 6, 4, 5, 7],
    [3, 1 / 5, 1, 2, 1 / 6, 1 / 4, 2, 1, 1, 2],
    [2, 1 / 5, 1 / 2, 1, 1 / 5, 1 / 2, 1, 1, 2, 3],
    [7, 1, 6, 5, 1, 3, 7, 4, 8, 8],
    [5, 1 / 2, 4, 2, 1 / 3, 1, 4, 3, 4, 5],
    [1, 1 / 6, 1 / 2, 1, 1 / 7, 1 / 4, 1, 1 / 2, 1, 1],
    [3, 1 / 4, 1, 1, 1 / 4, 1 / 3, 2, 1, 2, 3],
    [1, 1 / 5, 1, 1 / 2, 1 / 8, 1 / 4, 1, 1 / 2, 1, 2],
    [1 / 2, 1 / 7, 1 / 2, 1 / 3, 1 / 8, 1 / 5, 1, 1 / 3, 1 / 2, 1],
]

RI = [0, 0, 0, 0.5, 0.9, 1.12, 1.24, 1.32, 1.41, 1.45, 1.49]
