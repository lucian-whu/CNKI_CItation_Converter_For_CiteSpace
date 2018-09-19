#coding=utf-8
from cnki_excel_converter import CNKI_EXCEL_CONVERTOR
import helper

if __name__ == '__main__':
   # if helper.query_yes_no('你是否要搜索（否定会进入Excel转换）')
    your_cnki_to_excel_convertor = CNKI_EXCEL_CONVERTOR()
    your_cnki_to_excel_convertor.convert()
