#coding=utf-8
from cnki_excel_converter import CNKI_EXCEL_CONVERTOR
import helper
from excel_to_cssci import EXCEL_TO_CSSCI

if __name__ == '__main__':
    if helper.query_yes_no('你是否要立马开始搜索？（否定回进入Excel 转 CSSCI模式）'):
        your_cnki_to_excel_convertor = CNKI_EXCEL_CONVERTOR()
        your_cnki_to_excel_convertor.convert()
    else:
        data_dirs = helper.get_choices()
        for data_dir in data_dirs:
            e_to_c = EXCEL_TO_CSSCI(data_dir)
            e_to_c.convert()
