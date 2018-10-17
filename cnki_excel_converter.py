# coding=utf-8
from bs4 import BeautifulSoup
from urllib.request import urlopen
from urllib.parse import quote
from openpyxl import Workbook
import math
import os
import helper
import socket
from article_extractor import ARTICLE_EXTRACTOR
import urllib


class CNKI_EXCEL_CONVERTOR(object):
    """ CNKI_EXCEL_CONVERTOR"""

    def __init__(self):
        super(CNKI_EXCEL_CONVERTOR, self).__init__()
        self.search_paras = {
            "主题": "卓越教师",
            "篇名": "　",
            "作者": "　",
            "摘要": "　",
            "全文": "　",
        }
        self.search_urls = []
        self.soup = ""
        self.maxpage = 1
        self.num_per_page = 15
        self.filename_prefix = ""
        self.filename_postfix = "cnki_to_text"
        self.file_extension = ['.txt', '.xlsx']
        self.data_path = ''
        self.txt_name = ''
        self.excel_name = ''
        self.CSSCI_categories = ['【来源篇名】', '【英文篇名】', '【来源作者】',
                                 '【基    金】', '【期    刊】', '【第一机构】',
                                 '【机构名称】', '【第一作者】', '【中图类号】',
                                 '【年代卷期】', '【关 键 词】', '【基金类别】',
                                 '【参考文献】']
        self.filter_journals = ['课程.教材.教法']
        self.only_filter_or_phd = False

    def introduction(self):
        print("`你好，我来帮你把找到CNKI文献的参考文献数据吧！ 第一步我们要" +
              "将CNKI利用爬虫程序转换成一个txt文本文件和一个Excel表格文件，t" +
              "xt文件里是根据你限定的搜索方法得到的每一篇文献的网址和篇名，Exc" +
              "el文件将会是详细的信息。为了链接速度更快，请您最好使用教育网！\n 接下来，我们开始第一步！ \n")
        self.ask_for_search_parameters(self.search_paras)
        self.settle_filter()
        self.config_to_search_urls()
        print(self.search_urls)
        self.settle_filename()

    def settle_filter(self):
        self.ask_only_filter_or_phd()
        filename = self.get_filter_journals_filename()
        filepath = helper.get_file_path(os.getcwd(), filename)
        self.filter_journals = self.get_filter_journals(filepath)

    def ask_only_filter_or_phd(self):
        if helper.query_yes_no('您是否只需要自己设定的过滤期刊名称和硕博士论文？'):
            self.only_filter_or_phd = True
        else:
            self.only_filter_or_phd = False

    def get_filter_journals_filename(self):
        default_filename = 'journal_filter.txt'
        if os.path.exists(helper.get_file_path(os.getcwd(), default_filename)):
            if helper.query_yes_no('你想使用默认过滤期刊名文件吗？（默认文件名为 ‘' + default_filename + '’）'):
                return default_filename
        else:
            filename = input('请输入过滤期刊文件名：')
            if filename == '':
                print('文件不可为空！')
                return self.get_filter_journals_filename()
            return filename

    def get_filter_journals(self, filter_path):
        try:
            filter_journal_txt = open(filter_path, encoding='utf-8')
            lines = filter_journal_txt.readlines()
            lines[0] = lines[0][1:]
            return list(set(line.strip() for line in lines))
        except OSError:
            print('没找到该文件！请重新输入过滤期刊名文件名称。')
            self.get_filter_journals(self.get_filter_journals_filename())

    def is_in_filter_or_phd(self, first_institute, journal):
        return (journal in self.filter_journals and journal != '') or (first_institute == journal and first_institute != '')

    def get_maxpage(self):
        try:
            max_item = helper.get_num_from_re(
                self.soup.find('span', class_="page-sum").get_text())
            print('共搜索到' + str(max_item) + '篇文献')
            self.maxpage = math.ceil(max_item / self.num_per_page)
        except AttributeError:
            s = '抱歉，没有找到与您查询的'
            if s in self.soup.get_text():
                print("此期刊无相关文章")
                self.maxpage = 0
            else:
                self.maxpage = 1

    def ask_for_search_parameter(self, para, paras):
        answer = input(para + "(不填为默认" + para + ':' +
                       str(paras[para]) + ', 输入空格为不加入搜索范围):')
        if answer != '':
            paras[para] = answer

    def ask_for_search_parameters(self, paras):
        for para in paras.keys():
            self.ask_for_search_parameter(para, paras)

    def config_to_search_urls(self):
        paras_cn_en = {"主题": "theme",
                       "篇名": "title",
                       "作者": "author",
                       "摘要": "abstract",
                       "全文": "qw"
                       }
        config_copy = {}
        for para in self.search_paras.keys():
            if self.search_paras[para] == " ":
                pass
            else:
                config_copy[paras_cn_en[para]] = self.search_paras[para]

        url_keywords = ""
        self.filename_prefix = ""
        for para in config_copy.keys():
            self.filename_prefix += para[:2] + '-' + config_copy[para] + '-'
            if config_copy[para] != '\u3000':
                url_keywords += para + "%3a" + quote(config_copy[para]) + "+"
        for mg in self.filter_journals:
            self.search_urls.append("http://search.cnki.com.cn/search.aspx?q=" +
                                    url_keywords + 'magazine%3a' +
                                    quote(mg) + "&cluster=all&val=&rank=relevant&p=")
        #master and phd
        self.search_urls.append("http://search.cnki.com.cn/search.aspx?q=" +
                                url_keywords[:-1] +
                                "&rank=relevant&cluster=zyk&val=CMFDTOTAL&p=")
        self.search_urls.append("http://search.cnki.com.cn/search.aspx?q=" +
                                url_keywords[:-1] +
                                "&rank=relevant&cluster=zyk&val=CDFDTOTAL&p=")

    def update_soup(self, page_search_url):
        attempts = 0
        success = False
        while attempts < 50 and not success:
            try:
                html = urlopen(page_search_url)
                self.soup = BeautifulSoup(html, 'html.parser')
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

    def settle_filename(self):
        pwd = os.getcwd()
        self.data_path = pwd + "/" + self.filename_prefix +\
            self.filename_postfix + '-data'
        self.data_path = helper.mk_data_dir(self.data_path, 0)
        self.txt_name = self.get_txt_name()
        self.excel_name = self.get_excel_name()

    def get_search_results(self):
        txt = open(helper.get_file_path(self.data_path, self.txt_name),
                   'a+', encoding='utf-8')

        print("\n \t \t \t \t \t ************* 开始搜索页爬虫" +
              " ************* \t \t \t \t \t \n")
        # store every search item in every page in the txt file
        print("\n \t \t \t \t \t ************* 开始按照期刊搜索" +
              " ************* \t \t \t \t \t \n")
        for i in range(len(self.search_urls)):
            if(i < len(self.filter_journals)):
                print(self.filter_journals[i])
            elif i == len(self.search_urls) - 2:
                print("\n \t \t \t \t \t ************* 开始硕士论文搜索搜索" +
                      " ************* \t \t \t \t \t \n")
            else:
                print("\n \t \t \t \t \t ************* 开始博士论文搜索" +
                      " ************* \t \t \t \t \t \n")
            search_url = self.search_urls[i]
            print(search_url)
            self.update_soup(search_url)
            # find page
            start_page = 0
            self.get_maxpage()
            end_page = self.maxpage
            print(end_page)
            for current_page in range(start_page, end_page):
                url_end_token = str(current_page * self.num_per_page)
                page_search_url = search_url + url_end_token
                self.update_soup(page_search_url)
                print('第' + str(current_page) + '页： \n' + page_search_url)
                items = self.soup.find_all('div', class_="wz_content")
                for item in items:
                    title_and_url = item.find('a')
                    title = title_and_url.get_text()
                    article_url = title_and_url.get('href')
                    print(article_url)
                    txt.write(article_url + '\t' + title + '\t' + '\n')
        txt.close()

    def get_filename(self, extention_index):
        extention = self.file_extension[extention_index]
        filename = self.filename_prefix + \
            self.filename_postfix + extention
        if helper.query_yes_no("\n您是否需要使用默认文件名？（默认文件名为" +
                               filename + ')'):
            return filename
        else:
            filename = input("输入你的文件名，文件后缀为 \" " + extention + '\" \n')
        if filename == "" or (not filename.endswith(extention)):
            print("文件不可为空!\n")
            return self.get_txt_name(extention_index)
        return filename

    def get_txt_name(self):
        return self.get_filename(0)

    def get_excel_name(self):
        return self.get_filename(1)

    def get_article_results(self):
        # load all the article urls and titles
        txt = open(helper.get_file_path(
            self.data_path, self.txt_name), encoding='utf-8')
        article_urls_and_titles = txt.readlines()

        # make a template for the excel according the CSSCI txt template
        excel_path = helper.get_file_path(self.data_path, self.excel_name)
        excel = Workbook()
        sheet = excel.active
        sheet.append(self.CSSCI_categories)
        print("\n \t \t \t \t \t ************* 开始文章详情页爬虫" +
              " ************* \t \t \t \t \t \n")

        # scrabber every article
        sum_article = len(article_urls_and_titles)
        print('共有' + str(sum_article) + '篇文章！')
        for i in range(sum_article):
            article_url_and_title = article_urls_and_titles[i]
            article_url_and_title_list = article_url_and_title.split(
                '\t')  # make the lines read a list
            article_url = article_url_and_title_list[0]
            print('第' + str(i + 1) + '篇文章：' + article_url)
            title = article_url_and_title_list[1]
            article = ARTICLE_EXTRACTOR(title, article_url)
            article_infos = [title, ''] + article.get_all_article_info()
            # print(article_infos)
            if self.only_filter_or_phd:
                if self.is_in_filter_or_phd(article_infos[5], article_infos[4]):
                    sheet.append(article_infos)
                else:
                    pass
            else:
                sheet.append(article_infos)
        excel.save(excel_path)
        txt.close()

    def convert(self):
        self.introduction()
        self.get_search_results()
        self.get_article_results()

# test = CNKI_EXCEL_CONVERTOR()
# #test.settle_filter()
# print(test.filter_journals)
