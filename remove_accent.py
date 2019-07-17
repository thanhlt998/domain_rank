import re
import json

from mysql_connection import select_domain_objects, update_meaning_word_rate

PATTERNS = {
    '[àáảãạăắằẵặẳâầấậẫẩ]': 'a',
    '[đ]': 'd',
    '[èéẻẽẹêềếểễệ]': 'e',
    '[ìíỉĩị]': 'i',
    '[òóỏõọôồốổỗộơờớởỡợ]': 'o',
    '[ùúủũụưừứửữự]': 'u',
    '[ỳýỷỹỵ]': 'y'
}


def convert(text):
    """
    Convert from 'Tieng Viet co dau' thanh 'Tieng Viet khong dau'
    text: input string to be converted
    Return: string converted
    """
    output = text
    for regex, replace in PATTERNS.items():
        output = re.sub(regex, replace, output)
        # deal with upper case
        output = re.sub(regex.upper(), replace.upper(), output)
    return output


def process(fn):
    with open(fn, mode='r', encoding='utf8') as f:
        removed_accent_lines = [convert(line) for line in f.readlines()]
        f.close()

    with open('dict/removed_accent_words.txt', mode='w', encoding='utf8') as f:
        for line in removed_accent_lines:
            f.write(line)
        f.close()


def get_word_dict(fn):
    result = {}
    with open(fn, mode='r', encoding='utf8') as f:
        for line in f:
            result[line.strip()] = True
        f.close()
    return result


def get_possible_word_list(s):
    possible_word_list = []

    token_list = s.split()
    length = len(token_list)

    for i in range(length):
        for j in range(i + 1, length + 1):
            possible_word_list.append(' '.join(token_list[i:j]))

    return possible_word_list


def get_rate_no_meaning_word_in_domain(s):
    parts = [part.strip() for part in s.split('.')]
    possible_word_list = []
    for part in parts:
        possible_word_list.extend(get_possible_word_list(part))
    no_meaning_word = 0
    for word in possible_word_list:
        if result_dict.get(word):
            no_meaning_word += 1
    return no_meaning_word / len(possible_word_list)


if __name__ == '__main__':
    # process('dict/Viet74K.txt')
    result_dict = {**get_word_dict('dict/removed_accent_words.txt'), **get_word_dict('dict/words.txt')}

    domains = select_domain_objects(contain_crawled_urls=False)

    domain_meaning_word_rate = []

    with open('meaning_word_rate.txt', mode='w', encoding='utf8') as f:
        with open('dict/parsing_domain_data.jsonl', mode='r', encoding='utf8') as fp:
            for line in fp:
                data = json.loads(line)
                rate = get_rate_no_meaning_word_in_domain(data['doc'])
                f.write(f"{data['domain']}\t{rate}\n")
                domain_meaning_word_rate.append((data['domain'], rate))
            fp.close()
        f.close()

    update_meaning_word_rate(domain_meaning_word_rate)


