import PyPDF2
import sqlite3
import re

conn = sqlite3.connect("C:\\Users\\jcarl\\PycharmProjects\\pdf-invoice-scraper\\invoice.db")
c = conn.cursor()

pdfFileObj = open("C:\\Users\\jcarl\\PycharmProjects\\pdf-invoice-scraper\\IN490924019.pdf", 'rb')
pdfReader = PyPDF2.PdfFileReader(pdfFileObj)
no_of_pages = pdfReader.getNumPages()
pdf_text = ''


def represents_int(s):
    try:
        int(s)
        return True
    except ValueError:
        return False


for page in range(no_of_pages):
    pageObj = pdfReader.getPage(page)
    pdf_text += pageObj.extractText()

long_list = pdf_text.splitlines()
short_list = long_list[16:-15]

# Save invoice # to variable
invoice_date = ''
invoice_no = ''
for line in long_list:
    if 'Invoice #' in line:
        invoice_no = line.replace('Invoice # ', '')
    elif 'Invoice Date' in line:
        invoice_date = line.replace('Invoice Date ', '')

markers = []
for index, line in enumerate(short_list):
    if represents_int(line):
        markers.append(index)

mark_first = markers[:-1]
mark_last = markers[1:]


for x, y in zip(mark_first, mark_last):
    cur_list = short_list[x:y]
    if y-x == 5:
        qty = cur_list[0]
        itm = cur_list[1]
        prc = cur_list[2].split()
        price = prc[0].replace('$', '')
        item_type = prc[1]
        price_total = cur_list[3].replace('$', '').strip()
        name_list = list(filter(None, cur_list[4].split('  ')))
        item_long = name_list[0]
        rep = {" ST": "", " BU": ""}
        rep = dict((re.escape(k), v) for k, v in rep.items())
        pattern = re.compile("|".join(rep.keys()))
        item = pattern.sub(lambda m: rep[re.escape(m.group(0))], item_long)
        sql = ''' INSERT INTO test(invoice,date,source,qty,itm,item,type,price,price_total)
        VALUES('{0}', '{1}', '{2}', {3}, '{4}', '{5}', '{6}', {7}, {8}) '''.format(invoice_no, invoice_date, 'Krueger',
                                                                                   qty, itm, item, item_type, price,
                                                                                   price_total)
        c.execute(sql)

    elif y-x == 6:
        qty = cur_list[0]
        itm = cur_list[1]
        prc = cur_list[2].split()
        price = prc[0].replace('$', '')
        item_type = prc[1]
        price_total = cur_list[3].replace('$', '').strip()
        name_list = list(filter(None, cur_list[4].split('  ')))
        item_long = name_list[0]
        rep = {" ST": "", " BU": ""}  # Consolidate into function
        rep = dict((re.escape(k), v) for k, v in rep.items())
        pattern = re.compile("|".join(rep.keys()))
        item = pattern.sub(lambda m: rep[re.escape(m.group(0))], item_long)
        desc = cur_list[5]
        sql = r'''INSERT INTO test(invoice, date, source, qty, itm, item, type, price, price_total, desc)
        VALUES('{0}', '{1}', '{2}', {3}, '{4}', '{5}', '{6}', {7}, {8}, '{9}')'''.format(invoice_no, invoice_date,
                                                                                        'Krueger', qty, itm, item,
                                                                                        item_type, price, price_total,
                                                                                        desc)
        c.execute(sql)

pdfFileObj.close()
conn.commit()
conn.close()
# Extract freight
