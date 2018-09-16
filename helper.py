import re
import sys
import os
import errno
from bs4 import BeautifulSoup
from urllib.request import urlopen


def get_what_you_want_from_re(pattern, txt):
    return ''.join(re.findall(pattern, txt))


def get_num_from_re(txt):
    return int(get_what_you_want_from_re("[0-9]*", txt))


def query_yes_no(question, default="yes"):
    """Ask a yes/no question via raw_input() and return their answer.

    "question" is a string that is presented to the user.
    "default" is the presumed answer if the user just hits <Enter>.
        It must be "yes" (the default), "no" or None (meaning
        an answer is required of the user).

    The "answer" return value is True for "yes" or False for "no".
    """
    valid = {"yes": True, "y": True, "ye": True,
             "no": False, "n": False}
    if default is None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)

    while True:
        sys.stdout.write(question + prompt)
        choice = input().lower()
        if default is not None and choice == '':
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            sys.stdout.write("Please respond with 'yes' or 'no' "
                             "(or 'y' or 'n').\n")


def mk_data_dir(path, count):
    try:
        os.mkdir(path)
    except OSError as e:
        if e.errno == errno.EEXIST:
            count += 1
            if count > 1:
                path = path[:-2]  # delete the previous count token
            path += "_" + str(count)
            path = mk_data_dir(path, count)
        else:
            raise
    return path


def get_file_path(upper_path, filename):
    return upper_path + '/' + filename


def is_in_soup_txt(txt, soup_txt):
    if soup_txt == '':
        return False
    else:
        return txt in soup_txt


def is_not_in_soup_txt(txt, soup_txt):
    if soup_txt == '':
        return True
    else:
        return txt not in soup_txt


def join_with_splash(to_be_joined):
    if len(to_be_joined) == 1:
        return ''.join(to_be_joined)
    else:
        return '/'.join(to_be_joined)


def split_with_semi_colon(to_be_split):
    for i in range(len(to_be_split)):
        name = to_be_split[i]
        splited = name.split(';')
        try:
            splited.remove('')
        except ValueError:
            pass
        to_be_split = to_be_split[:i] + \
            splited + to_be_split[(i + 1):]
    return to_be_split


def get_nth_element(lst, n):
    if n >= len(lst):
        return ''
    else:
        return lst[n]
