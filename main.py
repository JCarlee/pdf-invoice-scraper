import PyPDF2
import sqlite3
from sqlite3 import Error

import sqlite3
from sqlite3 import Error

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
    for i in short_list[x:y]:
        if y-x == 5:
            pass
        elif y-x == 6:
            pass


# Loop through line items
# Loop SQL statements for line items
# Extract freight
pdfFileObj.close()
