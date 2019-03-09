# John Carlee
# JCarlee@gmail.com
# http://www.daffodilparker.com

import PyPDF2
import sqlite3
from time import strptime
import os
from tkinter import filedialog
from tkinter import *
import pathlib
import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials

master = Tk()
master.title("dp Invoice")
conn = None
c = None
now = datetime.datetime.now()


def connect_db():
    """Connect to SQLite Database"""
    global c
    global conn
    dir_path = os.getcwd()  # Where main.py lives
    conn = sqlite3.connect(dir_path + "\\" + "invoice.db")  # Connect to DB in main directory
    c = conn.cursor()
    print('Connected to ' + dir_path + "\\" + "invoice.db")


def close_connection():
    """Close connection to Database"""
    conn.commit()
    conn.close()
    print('Connection closed.')


# Check if string is actually an int
def represents_int(s):
    """Check if string should be integer"""
    try:
        int(s)
        return True
    except ValueError:
        return False


def select_file_list():
    """Create list of file paths if ending in .pdf"""
    try:
        files_output = []
        local_path = filedialog.askdirectory()
        for file in os.listdir(local_path):
                filename = os.fsdecode(file)
                if filename.endswith(".pdf"):
                    files_output.append(local_path + '\\' + filename)
                else:
                    pass
        dir_loop(files_output, local_path)
    except:
        print("Failure")
        pass


def select_pdfs():
    """Create list of files from direct selection"""
    files_output = filedialog.askopenfilenames(title="Select file", filetypes=(("PDF files", "*.pdf"),
                                                                               ("all files", "*.*")))
    sad = pathlib.Path(files_output[0])
    local_path = str(sad.parent)
    dir_loop(files_output, local_path)


def calc_avg():
    """Query for weighted price averages and write to Google Sheet"""
    sql_avg = """SELECT itm, item, SUM(qty), SUM(QTY * price) / SUM(qty)
    FROM items
    Where credit = 0
    GROUP BY itm;"""
    c.execute(sql_avg)
    rows = c.fetchall()
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    credentials = ServiceAccountCredentials.from_json_keyfile_name('DP Invoice-fb57448f59de.json', scope)
    gc = gspread.authorize(credentials)
    avg_sheet = gc.open('dp Invoice Database').worksheet("Average")
    row_end = str(len(rows) + 1)
    itm_range = avg_sheet.range('A2:A' + row_end)
    item_range = avg_sheet.range('B2:B' + row_end)
    count_range = avg_sheet.range('C2:C' + row_end)
    avg_range = avg_sheet.range('D2:D' + row_end)
    for row, itm, item, count, avg in zip(rows, itm_range, item_range, count_range, avg_range):
        itm.value, item.value, count.value, avg.value = row[0], row[1], row[2], row[3]
    avg_sheet.update_cells(itm_range)
    avg_sheet.update_cells(item_range)
    avg_sheet.update_cells(count_range)
    avg_sheet.update_cells(avg_range)
    print("Google Sheet Updated")


def kreuger_invoice_info(lng_lst):
    """Extract Invoice number and date from PDF"""
    invoice_number = ''
    invoice_myd = ''
    for z in lng_lst:
        if 'Invoice #' in z:
            invoice_number = z.replace('Invoice # ', '')
        elif 'Invoice Date' in z:
            invoice_myd = z.replace('Invoice Date ', '')
        elif 'Credit #' in z:
            invoice_number = z.replace('Credit # ', '')
    invoice_year = invoice_myd[-4:]
    invoice_mnth = invoice_myd[:3]
    invoice_month = strptime(invoice_mnth, '%b').tm_mon
    invoice_day = invoice_myd[4:6]
    return invoice_number, invoice_myd, invoice_year, invoice_month, int(invoice_day)


def negative_val(val1):
    """Change a value to negative"""
    price1 = -float(val1)
    return price1


def define_bunch(current_list):
    """Define multiple variables for insert statement"""
    qty_fn = current_list[0]
    itm_fn = current_list[1]
    prc_fn = current_list[2].split()
    price_fn = prc_fn[0].replace('$', '')
    item_type_fn = prc_fn[1]
    price_total_raw_fn = current_list[3]
    return qty_fn, itm_fn, prc_fn, price_fn, item_type_fn, price_total_raw_fn


def no_desc_sql(invoice_no, invoice_date, year, month, day, qty, itm, item, item_type, price, price_total, taxable,
                file_name):
    """SQL statement execution if no description"""
    sql_five = '''INSERT INTO item_test(invoice, date, year, month, day, source, qty, itm, item, type, price, 
    price_total, taxable, file, date_added)
    VALUES('{0}', '{1}', {2}, {3}, {4}, '{5}', {6}, '{7}', '{8}', '{9}', {10}, {11}, {12}, '{13}', '{14}');''' \
        .format(invoice_no, invoice_date, year, month, day, 'Krueger', qty, itm, item, item_type, price,
                price_total, taxable, file_name, now.strftime("%Y-%m-%d %H:%M"))
    c.execute(sql_five)


def desc_sql(c_list, invoice_no, invoice_date, year, month, day, qty, itm, item, item_type, price, price_total, taxable,
             file_name):
    """SQL statement execution if description exists"""
    desc = c_list[5]
    sql_desc = '''INSERT INTO item_test(invoice, date, year, month, day, source, qty, itm, item, type, price, 
    price_total, taxable, desc, file, date_added)
          VALUES('{0}', '{1}', {2}, {3}, {4}, '{5}', {6}, '{7}', '{8}', '{9}', {10}, {11}, {12}, '{13}', '{14}', '{15}');''' \
        .format(invoice_no, invoice_date, year, month, day, 'Krueger', qty, itm, item, item_type, price,
                price_total, taxable, desc, file_name, now.strftime("%Y-%m-%d %H:%M"))
    c.execute(sql_desc)


def freight_sql(lng_lst, frt_index, invoice_no, invoice_date, year, month, day, file_name):
    """SQL statement for freight table"""
    freight_price = lng_lst[frt_index].replace('$', '').strip()
    sql_freight = '''INSERT INTO freight_test(invoice_no, invoice_date, year, month, day, price, source, file, 
    date_added)
                VALUES('{0}', '{1}', {2}, {3}, {4}, {5}, '{6}', '{7}', '{8}');''' \
        .format(invoice_no, invoice_date, year, month, day, freight_price, 'Krueger', file_name,
                now.strftime("%Y-%m-%d %H:%M"))
    c.execute(sql_freight)


def dir_loop(files_output, local_path):
    rep = {" ST": "", " BU": "", " PC": "", "'": ""}
    rep = dict((re.escape(k), v) for k, v in rep.items())
    pattern = re.compile("|".join(rep.keys()))
    rep2 = {"$": "", ",": ""}
    rep2 = dict((re.escape(g), h) for g, h in rep2.items())
    pattern2 = re.compile("|".join(rep2.keys()))
    files, pdf_path = files_output, local_path
    short_list = []
    total_items = 0
    freight_invoice = ''
    frt_index = 0
    for pdf in files:
        pdf_file_obj = open(pdf, 'rb')
        pdf_reader = PyPDF2.PdfFileReader(pdf_file_obj)
        no_of_pages = pdf_reader.getNumPages()
        pdf_text = ''
        for page in range(no_of_pages):
            page_obj = pdf_reader.getPage(page)
            pdf_text += page_obj.extractText()
        long_list = pdf_text.splitlines()
        for index, line in enumerate(long_list):
            if 'Freight' in line:
                frt_index = index + 1
        if 'Invoice #' in long_list[4]:
            short_list = long_list[16:-15]
        elif 'Credit #' in long_list:
            short_list = long_list[16:-9]
        invoice_no, invoice_date, year, month, day = kreuger_invoice_info(long_list)
        name_check = [1]
        markers = []
        for index, line in enumerate(short_list):
            if represents_int(line) and (index - name_check[-1] != 1):
                markers.append(index)
                name_check.append(index)
        mark_first = markers[:-1]
        mark_last = markers[1:]
        file_name = pdf[len(pdf_path) + 1:-len('.pdf')]
        for x, y in zip(mark_first, mark_last):
            cur_list = short_list[x:y]
            qty, itm, prc, price, item_type, price_total_raw = define_bunch(cur_list)
            price_total = pattern2.sub(lambda m: rep2[re.escape(m.group(0))], price_total_raw)
            taxable = 0
            if 'T' in cur_list[3]:
                taxable = 1
                price_total = price_total.replace('T', '')
            if "Credit Invoice" in long_list[3]:
                price, price_total = negative_val(price), negative_val(price_total)
            name_list = list(filter(None, cur_list[4].split('  ')))
            item_long = name_list[0]
            item = pattern.sub(lambda m: rep[re.escape(m.group(0))], item_long)
            # print(invoice_no, ' | ', invoice_date, ' | ', 'Krueger', ' | ', qty, ' | ', itm, ' | ', item, ' | ',
            #       item_type, ' | ', price, ' | ', price_total, ' | ', file_name)
            if y - x == 5:
                total_items += 1
                no_desc_sql(invoice_no, invoice_date, year, month, day, qty, itm, item, item_type, price,
                            price_total, taxable, file_name)
            elif y-x == 6:
                total_items += 1
                desc_sql(cur_list, invoice_no, invoice_date, year, month, day, qty, itm, item, item_type, price,
                         price_total, taxable, file_name)
            if "Freight" in long_list and file_name != freight_invoice:
                freight_invoice = file_name
                freight_sql(long_list, frt_index, invoice_no, invoice_date, year, month, day, file_name)
        pdf_file_obj.close()
    print(total_items)


Button(master, text='Connect to DB', command=connect_db).grid(row=0, column=1, columnspan=2, sticky=E+W, pady=4,
                                                              padx=10)
Button(master, text='Process PDF Directory', command=select_file_list).grid(row=1, column=1, sticky=W, pady=4,
                                                                            padx=(10, 5))
Button(master, text='Process Specific PDFs', command=select_pdfs).grid(row=1, column=2, sticky=E, pady=4, padx=(5, 10))

Button(master, text='Commit and Close Connection', command=close_connection).grid(row=2, column=1, columnspan=2,
                                                                                  sticky=W+E, pady=4, padx=10)
Button(master, text='Calculate Weighted Averages', command=calc_avg).grid(row=3, column=1, columnspan=2,
                                                                          sticky=W+E, pady=4, padx=10)
Button(master, text='Quit', command=master.destroy).grid(row=4, column=1, columnspan=2, sticky=W+E, pady=4, padx=10)

mainloop()
