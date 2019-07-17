import os
import json
from bloom_filter import BloomFilter
from utils import get_domain


def check():
    bloom_filter = BloomFilter(max_elements=2000000, error_rate=0.0001)
    with open('urls.jsonl', mode='w') as f:
        for file_name in os.listdir("url_outlinks"):
            with open(f"url_outlinks/{file_name}", mode='r') as fp:
                data = json.load(fp)

                for domain, obj in data.items():
                    for url, outlinks in obj.items():
                        if url not in bloom_filter:
                            f.write(
                                f"""{json.dumps({"url": url, "no_outlinks": len(outlinks), "outlinks": outlinks})}\n""")
                            bloom_filter.add(url)

                fp.close()
            f.flush()
        f.close()


def get_urls():
    bloom_filter = BloomFilter(max_elements=2000000, error_rate=0.0001)
    with open('url_no_outlinks.txt', mode='w') as f:
        for file_name in os.listdir("url_outlinks"):
            with open(f"url_outlinks/{file_name}", mode='r') as fp:
                data = json.load(fp)

                for domain, obj in data.items():
                    for url, outlinks in obj.items():
                        if url not in bloom_filter:
                            f.write(f"""{url}\t{len(outlinks)}\n""")
                            bloom_filter.add(url)

                fp.close()
            f.flush()
        f.close()


def get_urls_income_links():
    urls = {}
    i = 0
    with open('url_no_outlinks.txt', mode='r') as f:
        for line in f:
            url_no_outlinks = line.strip().split("\t")
            obj = urls.setdefault(url_no_outlinks[0], {})
            obj['no_outlinks'] = int(url_no_outlinks[1])
            obj['index'] = i
            i += 1
        f.close()

    with open('urls.jsonl', mode='r') as f:
        for line in f:
            url_outlinks = json.loads(line)
            for outlink in url_outlinks['outlinks']:
                obj = urls.get(outlink)
                if obj:
                    income_links = obj.setdefault("income_links_index", [])
                    income_links.append(urls[url_outlinks['url']]['index'])
        f.close()

    with open("url_no_outlinks_income_links.jsonl", mode='w') as f:
        for url, obj in urls.items():
            f.write(f"{json.dumps({'url': url, **obj})}\n")
            f.flush()
        f.close()


def domain_out_domains():
    with open('domain_out_domains.jsonl', mode='w') as f:
        for file_name in os.listdir('url_outlinks'):
            with open(f"url_outlinks/{file_name}") as fp:
                domains = json.load(fp)
                for domain, url_outlinks in domains.items():
                    out_domains_set = set()
                    for outlinks in url_outlinks.values():
                        for outlink in outlinks:
                            out_domains_set.add(get_domain(outlink))
                    f.write(f"{json.dumps({'domain': domain, 'out_domains': list(out_domains_set)})}\n")

                fp.close()
            f.flush()
        f.close()


if __name__ == '__main__':
    # get_urls_income_links()
    # get_urls()
    # check()
    domain_out_domains()
