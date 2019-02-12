# NOTES:
# ONLY SUPPORTS KRUEGER INVOICES
# RUNNING THIS WILL ADD NEW RECORDS WITHOUT CHECKING FOR DUPLICATES

# TO DO:
# Check for duplicates before
# IN490810010 Random barcode


import PyPDF2
import sqlite3
import re
import os

dir_path = os.getcwd()                                                     # Where main.py lives
directory = os.fsencode(dir_path)
conn = sqlite3.connect(dir_path + "invoice.db")                            # Connect to DB in main directory
c = conn.cursor()
pdf_path = 'D:\\Google Drive\\DaffodilParkerInvoice'


# Check if string is actually an int
def represents_int(s):
    try:
        int(s)
        return True
    except ValueError:
        return False


files = []
for file in os.listdir(pdf_path):
    filename = os.fsdecode(file)
    if filename.endswith(".pdf"):
        files.append(pdf_path + '\\' + filename)
    else:
        pass

qty = 0
for pdf in files:
    pdfFileObj = open(pdf, 'rb')
    pdfReader = PyPDF2.PdfFileReader(pdfFileObj)
    no_of_pages = pdfReader.getNumPages()
    pdf_text = ''
    for page in range(no_of_pages):
        pageObj = pdfReader.getPage(page)
        pdf_text += pageObj.extractText()
    long_list = pdf_text.splitlines()
    short_list = long_list[16:-15]
    invoice_date = ''
    invoice_no = ''
    for line in long_list:
        if 'Invoice #' in line:
            invoice_no = line.replace('Invoice # ', '')
        elif 'Invoice Date' in line:
            invoice_date = line.replace('Invoice Date ', '')
    markers = []
    name_check = [1]
    for index, line in enumerate(short_list):
        if represents_int(line) and (index - name_check[-1] != 1):         # Account for int product names
            markers.append(index)
            name_check.append(index)
    mark_first = markers[:-1]
    mark_last = markers[1:]
    file_name = pdf[len(pdf_path) + 1:-len('.pdf')]
    rep = {" ST": "", " BU": "", " PC": ""}
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
        price_total = cur_list[3].replace('$', '').strip()
        if "Credit Invoice" in long_list[3]:
            price = price * -1
            price_total = price_total * -1
        name_list = list(filter(None, cur_list[4].split('  ')))
        item_long = name_list[0]
        item = pattern.sub(lambda m: rep[re.escape(m.group(0))], item_long)
        if y - x == 5:
            sql = ''' INSERT INTO test(invoice,date,source,qty,itm,item,type,price,price_total,file)
            VALUES('{0}', '{1}', '{2}', {3}, '{4}', '{5}', '{6}', {7}, {8}, '{9}') '''\
                .format(invoice_no, invoice_date, 'Krueger', qty, itm, item, item_type, price, price_total, file_name)
            # c.execute(sql)
        elif y-x == 6:
            desc = cur_list[5]
            sql = r'''INSERT INTO test(invoice, date, source, qty, itm, item, type, price, price_total, desc, file)
                  VALUES('{0}', '{1}', '{2}', {3}, '{4}', '{5}', '{6}', {7}, {8}, '{9}', '{10}')'''\
                .format(invoice_no, invoice_date, 'Krueger', qty, itm, item, item_type, price, price_total, desc,
                        file_name)
            # c.execute(sql)
        if "Freight" in long_list:
            freight_price = long_list[-12]
            sql = r'''INSERT INTO freight_test(invoice_no, invoice_date, price, source, file)
            VALUES('{0}', '{1}', '{2}', {3}, '{4}')'''\
            .format(invoice_no, invoice_date, freight_price, 'Krueger', file_name)
            # c.execute(sql)
    pdfFileObj.close()
# conn.commit()
conn.close()
