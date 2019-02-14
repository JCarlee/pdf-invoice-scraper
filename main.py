# NOTES:
# ONLY SUPPORTS KRUEGER INVOICES
# RUNNING THIS WILL ADD NEW RECORDS WITHOUT CHECKING FOR DUPLICATES

# TO DO:
# Check for duplicates before inserting - by creating unique identifier field in DB
# IN490810010 Random barcode (quarantined from PDFs)
# Handle T after price (waiting on DP and Krueger, quarantined from PDFs)

# John Carlee
# JCarlee@gmail.com
# http://www.daffodilparker.com

import PyPDF2
import sqlite3
import re
import os

dir_path = os.getcwd()                                                     # Where main.py lives
conn = sqlite3.connect(dir_path + "\\" + "invoice.db")                     # Connect to DB in main directory
c = conn.cursor()
pdf_path = 'D:\\Google Drive\\DaffodilParkerInvoice'
short_list = []
freight_invoice = ''
rep = {" ST": "", " BU": "", " PC": "", "'": ""}
rep = dict((re.escape(k), v) for k, v in rep.items())
pattern = re.compile("|".join(rep.keys()))
rep2 = {"$": "", ",": ""}
rep2 = dict((re.escape(g), h) for g, h in rep2.items())
pattern2 = re.compile("|".join(rep2.keys()))


# Check if string is actually an int
def represents_int(s):
    """Check if string should be integer"""
    try:
        int(s)
        return True
    except ValueError:
        return False


def create_file_list():
    """Create list of file paths if ending in .pdf"""
    files_output = []
    for file in os.listdir(pdf_path):
        filename = os.fsdecode(file)
        if filename.endswith(".pdf"):
            files_output.append(pdf_path + '\\' + filename)
        else:
            pass
    return files_output


def kreuger_invoice_info(lng_lst):
    """Extract Invoice number and date from PDF"""
    invoice_number = ''
    invoice_day = ''
    for z in lng_lst:
        if 'Invoice #' in z:
            invoice_number = z.replace('Invoice # ', '')
        elif 'Invoice Date' in z:
            invoice_day = z.replace('Invoice Date ', '')
        elif 'Credit #' in z:
            invoice_number = z.replace('Credit # ', '')
    return invoice_number, invoice_day


def negative_val(val1):
    price1 = -float(val1)
    return price1


def define_bunch(current_list):
    qty_fn = current_list[0]
    itm_fn = current_list[1]
    prc_fn = current_list[2].split()
    price_fn = prc_fn[0].replace('$', '')
    item_type_fn = prc_fn[1]
    price_total_raw_fn = current_list[3]
    return qty_fn, itm_fn, prc_fn, price_fn, item_type_fn, price_total_raw_fn


files = create_file_list()


for pdf in files:
    pdfFileObj = open(pdf, 'rb')
    pdfReader = PyPDF2.PdfFileReader(pdfFileObj)
    no_of_pages = pdfReader.getNumPages()
    pdf_text = ''
    for page in range(no_of_pages):
        pageObj = pdfReader.getPage(page)
        pdf_text += pageObj.extractText()
    long_list = pdf_text.splitlines()                               # Split PDF text into list
    if 'Invoice #' in long_list[4]:
        short_list = long_list[16:-15]
    elif 'Credit #' in long_list:
        short_list = long_list[16:-9]
    invoice_no, invoice_date = kreuger_invoice_info(long_list)
    name_check = [1]
    markers = []
    for index, line in enumerate(short_list):
        if represents_int(line) and (index - name_check[-1] != 1):  # Account for numeric product names
            markers.append(index)
            name_check.append(index)
    mark_first = markers[:-1]
    mark_last = markers[1:]
    file_name = pdf[len(pdf_path) + 1:-len('.pdf')]
    for x, y in zip(mark_first, mark_last):
        cur_list = short_list[x:y]
        # if 'T' in cur_list[3]:
        #     print(pdf)
        qty, itm, prc, price, item_type, price_total_raw = define_bunch(cur_list)
        price_total = pattern2.sub(lambda m: rep2[re.escape(m.group(0))], price_total_raw)
        if "Credit Invoice" in long_list[3]:
            price, price_total = negative_val(price), negative_val(price_total)
        name_list = list(filter(None, cur_list[4].split('  ')))
        item_long = name_list[0]
        item = pattern.sub(lambda m: rep[re.escape(m.group(0))], item_long)
        # print(invoice_no, ' | ', invoice_date, ' | ', 'Krueger', ' | ', qty, ' | ', itm, ' | ', item, ' | ',
        #       item_type, ' | ', price, ' | ', price_total, ' | ', file_name)
        if y - x == 5:
            sql = '''INSERT INTO test(invoice, date, source, qty, itm, item, type, price, price_total, file)
            VALUES('{0}', '{1}', '{2}', {3}, '{4}', '{5}', '{6}', {7}, {8}, '{9}');'''\
                .format(invoice_no, invoice_date, 'Krueger', qty, itm, item, item_type, price, price_total, file_name)
            c.execute(sql)
        elif y-x == 6:
            desc = cur_list[5]
            sql = '''INSERT INTO test(invoice, date, source, qty, itm, item, type, price, price_total, desc, file)
                  VALUES('{0}', '{1}', '{2}', {3}, '{4}', '{5}', '{6}', {7}, {8}, '{9}', '{10}');'''\
                .format(invoice_no, invoice_date, 'Krueger', qty, itm, item, item_type, price, price_total, desc,
                        file_name)
            c.execute(sql)
        if "Freight" in long_list and file_name != freight_invoice:
            freight_invoice = file_name
            freight_price = long_list[-12]
            sql = '''INSERT INTO freight_test(invoice_no, invoice_date, price, source, file)
            VALUES('{0}', '{1}', '{2}', '{3}', '{4}');'''\
            .format(invoice_no, invoice_date, freight_price, 'Krueger', file_name)
            c.execute(sql)
    pdfFileObj.close()
conn.commit()
conn.close()
