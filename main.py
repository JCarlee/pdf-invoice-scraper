# NOTES:
# ONLY SUPPORTS KRUEGER INVOICES
# RUNNING THIS WILL ADD NEW RECORDS WITHOUT CHECKING FOR DUPLICATES

# TO DO:
# Check for duplicates before inserting
# IN490810010 Random barcode
# Handle T after price

# John Carlee
# JCarlee@gmail.com

# http://www.daffodilparker.com

import PyPDF2
import sqlite3
import re
import os

dir_path = os.getcwd()                                                     # Where main.py lives
directory = os.fsencode(dir_path)
conn = sqlite3.connect(dir_path + "\\" + "invoice.db")                            # Connect to DB in main directory
c = conn.cursor()
pdf_path = 'D:\\Google Drive\\DaffodilParkerInvoice'
short_list = []


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


def kreuger_invoice_info(jah):
    invoice_number = ''
    invoice_day = ''
    for z in jah:
        if 'Invoice #' in z:
            invoice_number = z.replace('Invoice # ', '')
        elif 'Invoice Date' in z:
            invoice_day = z.replace('Invoice Date ', '')
        elif 'Credit #' in z:
            invoice_number = z.replace('Credit # ', '')
    return invoice_number, invoice_day


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
        if represents_int(line) and (index - name_check[-1] != 1):  # Account for int product names
            markers.append(index)
            name_check.append(index)
    mark_first = markers[:-1]
    mark_last = markers[1:]
    file_name = pdf[len(pdf_path) + 1:-len('.pdf')]
    rep = {" ST": "", " BU": "", " PC": "", "'": ""}
    rep = dict((re.escape(k), v) for k, v in rep.items())
    pattern = re.compile("|".join(rep.keys()))
    for x, y in zip(mark_first, mark_last):
        cur_list = short_list[x:y]
        if 'T' in cur_list[3]:
            print(pdf)
        qty = cur_list[0]
        itm = cur_list[1]
        prc = cur_list[2].split()
        price = prc[0].replace('$', '')
        item_type = prc[1]
        price_total_raw = cur_list[3]
        rep2 = {"$": "", ",": ""}
        rep2 = dict((re.escape(g), h) for g, h in rep2.items())
        pattern2 = re.compile("|".join(rep2.keys()))
        price_total = pattern2.sub(lambda m: rep2[re.escape(m.group(0))], price_total_raw)
        if "Credit Invoice" in long_list[3]:
            price = -float(price)
            price_total = -float(price_total)
        name_list = list(filter(None, cur_list[4].split('  ')))
        item_long = name_list[0]
        item = pattern.sub(lambda m: rep[re.escape(m.group(0))], item_long)
        print(invoice_no, ' | ', invoice_date, ' | ', 'Krueger', ' | ', qty, ' | ', itm, ' | ', item, ' | ', item_type, ' | ', price, ' | ', price_total, ' | ', file_name)
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
        if "Freight" in long_list:
            freight_price = long_list[-12]
            sql = '''INSERT INTO freight_test(invoice_no, invoice_date, price, source, file)
            VALUES('{0}', '{1}', '{2}', '{3}', '{4}');'''\
            .format(invoice_no, invoice_date, freight_price, 'Krueger', file_name)
            c.execute(sql)
    pdfFileObj.close()
# conn.commit()
conn.close()
