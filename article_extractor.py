# coding=utf-8
from bs4 import BeautifulSoup
from urllib.request import urlopen
import helper
import socket
import re
import sys
sys.setrecursionlimit(100)


class ARTICLE_EXTRACTOR(object):
    """docstring for ARTICLE_EXTRACTOR"""

    def __init__(self, title, article_url):
        super(ARTICLE_EXTRACTOR, self).__init__()
        self.title = title
        self.article_url = article_url
        self.article_soup = ''
        self.success = False
        self.attempt_to_connect()
        self.misc_soup = ''
        self.misc_soup_list = []
        self.keywords_list = []
        self.misc_soup_txt = ''
        self.misc_soup_labels_list = []
        # usually contains information about 【作者单位】【基金】【分类号】
        self.source_authors_list = []
        self.institutes_list = []
        self.institutes_author_match_num = None
        if self.success:
            self.update_instance()

    def update_instance(self):
        if self.success:
            self.get_misc_soup()
            self.get_misc_soup_list()
            if self.success:
                self.misc_soup_txt = self.misc_soup.get_text()
                self.misc_soup_labels_list = self.get_misc_soup_list()
                self.misc_soup_labels_list = self.misc_soup.find_all('font')
                self.source_authors_list = self.get_source_authors_list()
                self.institutes_list = self.get_institutes_list()
                self.institutes_author_match_num = self.get_institutes_author_match_num()
                self.keywords_list = self.get_keywords_list()

    def get_source_authors(self):
        return helper.join_with_splash(self.source_authors_list)

    def get_misc_soup(self):
        if self.article_soup is not None:
            self.misc_soup = self.article_soup.find(
                'div', style='text-align:left;', class_='xx_font')
        else:
            try:
                attempt = 1
                while attempt < 50 and self.article_soup is None:
                    self.attempt_to_connect()
                self.get_misc_soup()
            except RuntimeError:
                print('网路故障，舍弃该文章。\n')

    def get_misc_soup_list(self):
        if self.misc_soup is not None:
            try:
                self.misc_soup_list = self.misc_soup.get_text(
                    u'/t').split('/t')[1:]
                self.misc_soup_list.remove('：\r\n                ')
            except ValueError:
                self.misc_soup_list = self.misc_soup.get_text(
                    u'/t').split('/t')[1:]
        else:
            try:
                attempt = 0
                while attempt < 50 and self.misc_soup is None:
                    self.get_misc_soup()
                    attempt += 1
                    if attempt == 50:
                        self.attempt_to_connect()
                        self.get_misc_soup()
                self.get_misc_soup_list()
            except RuntimeError:
                print('网络故障,舍弃该文章。\n')
                self.success = False

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
        try:
            institutes_list = self.get_misc_soup_content('【作者单位】')
            if institutes_list == []:
                raise ValueError
        except (ValueError, AttributeError):
            try:
                institutes_list = self.get_misc_soup_content('【作者单位】：')
                if institutes_list == []:
                    raise AttributeError
            except AttributeError:
                try:
                    institutes_list = self.get_misc_soup_content('【学位授予单位】：')
                    if institutes_list == []:
                        institutes_list = [self.misc_soup_list[1]]
                        if institutes_list[1] == '':
                            institutes_list = []
                except IndexError:
                    institutes_list = []
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
            if label_soup is None:
                # strengthen the stability
                return self.get_misc_soup_content(label)
            label_index = self.misc_soup_list.index(label)
            label_list_index = self.misc_soup_labels_list.index(label_soup)
            if label_list_index == len(self.misc_soup_labels_list) - 1:
                end_index = 1  # there is only one label
            else:
                end_list_index = label_list_index + 1
                end_soup = self.misc_soup_labels_list[end_list_index]
                end_index = self.misc_soup_list.index(end_soup.get_text())
            content_list = self.misc_soup_list[label_index + 1:end_index]
            return content_list
        else:
            return []

        # def get_time(self):

    def get_keywords(self):
        return helper.join_with_splash(self.keywords_list)

    def get_keywords_list(self):
        try:
            keyword_txt = self.article_soup.find("meta",
                                                 attrs={'name': 'autoKeywords'}).get('content')
            if ';' in keyword_txt:
                return keyword_txt.split(';')
            else:
                return keyword_txt.split(' ')
        except AttributeError:
            return []

    def get_time(self):
        try:
            time_text = self.article_soup.find(
                'font', color='#0080ff').get_text()
        except AttributeError:
            time_text = self.article_soup.find('font', color="#000").get_text()
        return re.search(r"[0-9]*", time_text).group()

    def get_fund_type(self):
        fund_source = self.get_funding_source()
        if '教育部' in fund_source:
            return '教育部基金/'
        elif '国' in fund_source and '社' in fund_source:
            return '国家社科基金/'
        elif '国' not in fund_source and '社' in fund_source:
            return '地方省市社科基金/'
        else:
            return ''

        # def get_citations(self):

    def get_classification_num(self):
        try:
            font_classification = self.misc_soup.find(
                text='【分类号】：')
            classification_num = font_classification.next_element
            if helper.hasNumbers(classification_num):
                return classification_num
            else:
                raise TypeError
        except (AttributeError, TypeError):
            return ''

    def get_journal(self):
        journal_soup = self.article_soup.find(
            'div', style="float:left;").find('b')
        return re.sub('[!《》]', '', journal_soup.get_text().strip())

    def get_citations(self):
        cankao_soup = self.article_soup.find(
            'div', id=['cankao', 'div_Ref'])
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
        if self.success:
            return [self.get_source_authors(), self.get_funding_source(),
                    self.get_journal(), self.get_first_institute(),
                    self.get_institutes_names(), self.get_first_author(),
                    self.get_classification_num(), self.get_time(),
                    self.get_keywords(), self.get_fund_type(), self.get_citations()]
        else:
            return ['', '', '', '', '', '', '', '', '', '', '']

    def attempt_to_connect(self):
        attempts = 0
        while attempts < 50 and not self.success:
            try:
                html = urlopen(self.article_url)
                self.article_soup = BeautifulSoup(html, 'html.parser')
                socket.setdefaulttimeout(10)  # 设置10秒后连接超时
                self.success = True
            except socket.error:
                attempts += 1
                print("第" + str(attempts) + "次重试！！")
                if attempts == 50:
                    self.success = False
                    print("此网页无法打开！")
                    break
            except OSError:
                attempts += 1
                print("第" + str(attempts) + "次重试！！")
                if attempts == 50:
                    self.success = False
                    print("此网页无法打开！")
                    break
            except RuntimeError:
                self.success = False
                print("此网页无法打开！")
                break

# # test = ARTICLE_EXTRACTOR(
# #     'sdfa', 'http://epub.cnki.net/grid2008/detail.aspx?filename=ZGJT201809022&dbname=CJFNPREP')


# test = ARTICLE_EXTRACTOR('dfas', 'http://cdmd.cnki.com.cn/Article/CDMD-10269-1014318220.htm')
# # test = ARTICLE_EXTRACTOR(
# #     'sdfa', 'http://cdmd.cnki.com.cn/Article/CDMD-10418-1017828685.htm')
# test = ARTICLE_EXTRACTOR(
#     'dsaf', 'http://youxian.cnki.com.cn/yxdetail.aspx?filename=YJSY201804010&dbname=CJFDPREP')
# test = ARTICLE_EXTRACTOR(
#     'dfa', 'http://cpfd.cnki.com.cn/Article/CPFDTOTAL-LGJX201704002011.htm')
# test = ARTICLE_EXTRACTOR(
#     'dsaf', 'http://www.cnki.com.cn/Article/CJFDTOTAL-ZXJJ201511026.htm')
# test = ARTICLE_EXTRACTOR(
#     'df', 'http://www.cnki.com.cn/Article/CJFDTOTAL-FLSH201506039.htm')
# test = ARTICLE_EXTRACTOR(
#     'dfaasdf', 'http://www.cnki.com.cn/Article/CJFDTOTAL-YDJY201309257.htm')
# test = ARTICLE_EXTRACTOR(
#     'asdffd', 'http://www.cnki.com.cn/Article/CJFDTOTAL-YDJY201310390.htm')
# test = ARTICLE_EXTRACTOR('dfas', 'http://www.cnki.com.cn/Article/CJFDTOTAL-ZYDC201516004.htm')
# test = ARTICLE_EXTRACTOR(
#     'DASF', 'http://www.cnki.com.cn/Article/CJFDTOTAL-YWTD201608025.htm')
#test = ARTICLE_EXTRACTOR('dsf', 'http://www.cnki.com.cn/Article/CJFDTOTAL-KWYW201522038.htm')
# test = ARTICLE_EXTRACTOR('dfa', 'http://www.cnki.com.cn/Article/CJFDTOTAL-ZYDC201519003.htm')
# test = ARTICLE_EXTRACTOR(
#     'dsfa', 'http://www.cnki.com.cn/Article/CJFDTOTAL-JXGL198704006.htm')
# test = ARTICLE_EXTRACTOR(
#     'sdfasg', 'http://youxian.cnki.com.cn/yxdetail.aspx?filename=CZSK201603013&dbname=CJFDPREN')
# test = ARTICLE_EXTRACTOR(
#     'sdf', 'http://cdmd.cnki.com.cn/CDMD/DetailNew.ashx?url=/Article/CDMD-10118-1016100574.htm')
# print(test.get_all_article_info())
