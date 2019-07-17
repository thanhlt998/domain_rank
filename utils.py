from urllib.parse import urlparse
import re


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
