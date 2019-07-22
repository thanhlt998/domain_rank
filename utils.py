from urllib.parse import urlparse
import re
from tld import get_tld


def get_domain_age_request_url(domain):
    return f"https://whois.inet.vn/api/whois/domainspecify/{domain}"


def get_domain_popularity_request_url(domain):
    return f"http://data.alexa.com/data?cli=10&dat=snbamz&url={domain}"


def get_url_with_scheme(domain):
    return ''.join(["http://", domain])


def get_ssl_info_url(domain, is_new_scan):
    # return f"https://api.ssllabs.com/api/v3/analyze?host={domain}&publish=on" \
    #     f"{'&startNew=on' if is_new_scan else ''}&all=done&ignoreMismatch=on"
    # return f"https://api.ssllabs.com/api/v3/analyze?host={domain}&hideResults=on"
    return "https://www.digicert.com/api/check-host.php"


def get_domain(url):
    return urlparse(url=url).netloc


def fix_url(url):
    if re.match(
            r'.*\.(css|js|bmp|gif|jpe?g|png|tiff?|mid|mp2|mp3|mp4|wav|avi|mov|mpeg|ram|m4v|pdf|rm|smil|wmv|swf|wma|zip|rar|gz|doc|docx|xls|xlsx)',
            url.lower()):
        return None
    return url


def get_no_sub_domains(domain):
    sub_domains = get_tld(get_url_with_scheme(domain), as_object=True).subdomain
    if sub_domains == '':
        no_sub_domains = 0
    else:
        no_sub_domains = sub_domains.count('.') + 1

    return no_sub_domains


def get_supplied_domain(domain):
    return get_tld(get_url_with_scheme(domain), as_object=True).domain
