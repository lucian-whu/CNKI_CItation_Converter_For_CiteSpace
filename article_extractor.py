from bs4 import BeautifulSoup
import urllib
from urllib.request import urlopen
import helper
import socket
import re


class ARTICLE_EXTRACTOR(object):
    """docstring for ARTICLE_EXTRACTOR"""

    def __init__(self, title, article_url):
        super(ARTICLE_EXTRACTOR, self).__init__()
        self.title = title
        self.article_url = article_url
        self.article_soup = ''
        self.attempt_to_connect()
        self.keywords_list = self.get_keywords_list()
        self.misc_soup = self.article_soup.find(
            'div', style='text-align:left;', class_='xx_font')
        self.misc_soup_list = self.misc_soup.find_all(['a', 'font'])
        self.misc_soup_txt = self.misc_soup.get_text()
        self.misc_soup_labels_list = self.misc_soup.find_all('font')
        # usually contains information about 【作者单位】【基金】【分类号】
        self.source_authors_list = self.get_source_authors_list()
        self.institutes_list = self.get_institutes_list()
        self.institutes_author_match_num =\
            self.get_institutes_author_match_num()

    def get_source_authors(self):
        authors_list = self.get_source_authors_list()
        return helper.join_with_splash(authors_list)

    def get_source_authors_list(self):
        authors_soup = self.article_soup.find(
            'div', style='text-align:center; width:740px; height:30px;')
        authors_soup = authors_soup.find_all('a')
        authors_list = []
        for author_soup in authors_soup:
            authors_list.append(author_soup.get_text())
        return authors_list

    def get_funding_source(self):
        return helper.join_with_splash(self.get_misc_soup_content('【基金】：'))

    def get_institutes_list(self):
        institutes_list = self.get_misc_soup_content('【作者单位】')
        return helper.split_with_semi_colon(institutes_list)

    def get_institutes_author_match_num(self):
        num_institutes = len(self.institutes_list)
        num_authors = len(self.source_authors_list)

        if num_institutes == 0:
            return 0
        elif num_institutes == num_authors:
            return num_institutes
        elif num_institutes < num_authors:
            return -1
        elif num_institutes > num_authors:
            return -1

    def get_institutes_names(self):
        institutes_name = ''
        if self.institutes_author_match_num > 0:
            for i in range(self.institutes_author_match_num):
                institutes_name += ('[' + self.source_authors_list[i] +
                                    ']' + self.institutes_list[i] + '/')
            return institutes_name[:-1]
        elif self.institutes_author_match_num == 0:
            return institutes_name
        elif self.institutes_author_match_num < 0:
            for author in self.source_authors_list:
                institutes_name += ('[' + author + ']' +
                                    self.institutes_list[0] + '/')
            return institutes_name[:-1]

    def get_first_author(self):
        if len(self.source_authors_list) == 0:
            return ''
        else:
            return self.source_authors_list[0]

    def get_misc_soup_content(self, label):
        if helper.is_in_soup_txt(label, self.misc_soup_txt):
            label_soup = self.misc_soup.find(
                text=label).find_parent().find_parent()
            label_index = self.misc_soup_list.index(label_soup)
            label_list_index = self.misc_soup_labels_list.index(label_soup)
            if label_list_index == len(self.misc_soup_labels_list) - 1:
                end_index = 1  # there is only one label
            else:
                end_list_index = label_list_index + 1
                end_soup = self.misc_soup_labels_list[end_list_index]
                end_index = self.misc_soup_list.index(end_soup)
            content_soup_list = self.misc_soup_list[label_index + 1:end_index]
            content_list = []
            for content_soup in content_soup_list:
                content_list.append(content_soup.get_text())
            return content_list
        else:
            return []

        # def get_time(self):

    def get_keywords(self):
        return helper.join_with_splash(self.keywords_list)

    def get_keywords_list(self):
        return self.article_soup.find(
            attrs={"name": "keywords"})['content'].split(' ')

    def get_time(self):
        time_text = self.article_soup.find('font', color='#0080ff').get_text()
        return re.search(r"[0-9]*", time_text).group()

    def get_fund_type(self):
        fund_source = self.get_funding_source()
        if '教育部' in fund_source:
            return '教育部基金/'
        elif '国' in fund_source and '社' in fund_source:
            return '国家社科基金/'
        else:
            return fund_source

        # def get_citations(self):

    def get_classification_num(self):
        font_classification = self.misc_soup.find(
            text='【分类号】：')
        classification_num = font_classification.next_element
        return classification_num

    def get_journal(self):
        journal_soup = self.article_soup.find(
            'div', style="float:left;").find('b')
        return re.sub('[!《》]', '', journal_soup.get_text().strip())

    def get_citations(self):
        cankao_soup = self.article_soup.find(
            'div', id='cankao')
        citations = ''
        if cankao_soup is not None:
            citations_soup = cankao_soup.find_all('td', width='676')
            for i in range(len(citations_soup)):
                citation_soup = citations_soup[i]
                title_soup = citation_soup.find('a')
                title = title_soup.get_text()[:-1]
                authors = title_soup.previous_element
                author = authors.split(';')[0]
                journal_time_list = citation_soup.get_text().split(';')[-2:]
                journal = journal_time_list[0]
                time = re.search(r"[0-9]*", journal_time_list[1]).group()
                citation_list = [author, title, journal, time]
                citations += str(i + 1) + "." + ".".join(citation_list) + '\n'
                i += 1
        return citations

    def get_first_institute(self):
        return helper.get_nth_element(self.institutes_list, 0)

    def get_all_article_info(self):
        return [self.get_source_authors(), self.get_funding_source(),
                self.get_journal(
        ), self.get_first_institute(), self.get_institutes_names(),
            self.get_first_author(), self.get_classification_num(), self.get_time(),
            self.get_keywords(), self.get_fund_type(), self.get_citations()]

    def attempt_to_connect(self):
        attempts = 0
        success = False
        while attempts < 50 and not success:
            try:
                html = urlopen(self.article_url)
                self.article_soup = BeautifulSoup(html, 'html.parser')
                socket.setdefaulttimeout(10)  # 设置10秒后连接超时
                success = True
            except socket.error:
                attempts += 1
                print("第" + str(attempts) + "次重试！！")
                if attempts == 50:
                    break
            except urllib.error:
                attempts += 1
                print("第" + str(attempts) + "次重试！！")
                if attempts == 50:
                    break

