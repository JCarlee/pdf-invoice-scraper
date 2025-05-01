import datetime
import os
import pathlib
import re
import sqlite3
from time import strptime
from tkinter import *
from tkinter import filedialog

import PyPDF2
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Global variables
db = None
GOOGLE_SCOPE = ['https://spreadsheets.google.com/feeds',
                'https://www.googleapis.com/auth/drive']


class DatabaseHandler:
    def __init__(self):
        self.conn = None
        self.cursor = None

    def connect(self):
        dir_path = os.getcwd()
        db_path = os.path.join(dir_path, "invoice.db")
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        print(f'Connected to {db_path}')

    def close(self):
        if self.conn:
            self.conn.commit()
            self.conn.close()
            print('Connection closed.')

    def execute(self, query):
        self.cursor.execute(query)

    def fetch_all(self, query):
        self.cursor.execute(query)
        return self.cursor.fetchall()


def connect_db():
    """Connect to SQLite Database using DatabaseHandler"""
    global db
    if db is not None:
        print('Already connected to database')
        return

    try:
        db = DatabaseHandler()
        db.connect()
    except Exception as e:
        print(f'Error connecting to database: {e}')
        raise


def close_connection():
    """Safely commit changes and close database connection"""
    global db

    try:
        if db is not None and db.conn is not None:
            db.close()
            print('Changes committed and connection closed successfully.')
        else:
            print('No active database connection to close.')
    except Exception as e:
        print(f'Error closing database connection: {e}')
        try:
            if hasattr(db, 'conn') and db.conn:
                db.conn.rollback()
                db.conn.close()
        except:
            pass
        raise
    finally:
        db = None


class SQLQueryBuilder:
    def __init__(self, source='Krueger'):
        self.source = source
        self.now = datetime.datetime.now()

    def build_item_query(self, invoice_no, invoice_date, year, month, day, qty, itm, item,
                        item_type, price, price_total, taxable, file_name, desc=None):
        if desc:
            return self._build_with_desc(invoice_no, invoice_date, year, month, day, qty,
                                       itm, item, item_type, price, price_total, taxable,
                                       file_name, desc)
        return self._build_without_desc(invoice_no, invoice_date, year, month, day, qty,
                                      itm, item, item_type, price, price_total, taxable,
                                      file_name)

    def build_freight_query(self, invoice_no, invoice_date, year, month, day, freight_price, file_name):
        return f'''INSERT INTO freight_test(invoice_no, invoice_date, year, month, day, price, source, file, date_added)
                VALUES('{invoice_no}', '{invoice_date}', {year}, {month}, {day}, {freight_price}, '{self.source}',
                '{file_name}', '{self.now.strftime("%Y-%m-%d %H:%M")}');'''


class PDFProcessor:
    def __init__(self, pdf_path):
        self.pdf_path = pdf_path
        self.file_name = os.path.basename(pdf_path)[:-4]

    def process_pdf(self):
        with open(self.pdf_path, 'rb') as pdf_file:
            pdf_reader = PyPDF2.PdfFileReader(pdf_file)
            pdf_text = '\n'.join(pdf_reader.getPage(page).extractText()
                               for page in range(pdf_reader.getNumPages()))

        long_list = pdf_text.splitlines()
        invoice_info = kreuger_invoice_info(long_list)

        if 'Invoice #' in long_list[4]:
            short_list = long_list[16:-15]
        elif 'Credit #' in long_list:
            short_list = long_list[16:-9]

        return long_list, short_list, invoice_info


class StringCleaner:
    def __init__(self):
        self.item_replacements = {" ST": "", " BU": "", " PC": "", "'": ""}
        self.price_replacements = {"$": "", ",": ""}

    def clean_item_name(self, text):
        pattern = re.compile("|".join(map(re.escape, self.item_replacements.keys())))
        return pattern.sub(lambda m: self.item_replacements[re.escape(m.group(0))], text)

    def clean_price(self, text):
        pattern = re.compile("|".join(map(re.escape, self.price_replacements.keys())))
        return pattern.sub(lambda m: self.price_replacements[re.escape(m.group(0))], text)


class InvoiceProcessorGUI:
    def __init__(self, master):
        self.master = master
        master.title("dp Invoice")

        Button(master, text='Connect to DB', command=connect_db).grid(
            row=0, column=0, columnspan=2, sticky='ew', padx=10, pady=4)

        Button(master, text='Process PDF Directory', command=select_file_list).grid(
            row=1, column=0, padx=10, pady=4)

        Button(master, text='Process Specific PDFs', command=select_pdfs).grid(
            row=1, column=1, padx=10, pady=4)

        Button(master, text='Commit and Close Connection', command=close_connection).grid(
            row=2, column=0, columnspan=2, sticky='ew', padx=10, pady=4)

        Button(master, text='Calculate Weighted Averages', command=calc_avg).grid(
            row=3, column=0, columnspan=2, sticky='ew', padx=10, pady=4)

        Button(master, text='Quit', command=master.destroy).grid(
            row=4, column=0, columnspan=2, sticky='ew', padx=10, pady=4)


def represents_int(s):
    """Check if string should be integer"""
    try:
        int(s)
        return True
    except ValueError:
        return False


def negative_val(val1):
    """Change a value to negative"""
    return -float(val1)


def define_bunch(current_list):
    """Define multiple variables for insert statement"""
    qty_fn = current_list[0]
    itm_fn = current_list[1]
    prc_fn = current_list[2].split()
    price_fn = prc_fn[0].replace('$', '')
    item_type_fn = prc_fn[1]
    price_total_raw_fn = current_list[3]
    return qty_fn, itm_fn, prc_fn, price_fn, item_type_fn, price_total_raw_fn


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


def select_file_list():
    """Create list of file paths if ending in .pdf"""
    try:
        files_output = []
        local_path = filedialog.askdirectory()
        for file in os.listdir(local_path):
            filename = os.fsdecode(file)
            if filename.endswith(".pdf"):
                files_output.append(os.path.join(local_path, filename))
        dir_loop(files_output, local_path)
    except Exception as e:
        print(f"Failure: {e}")


def select_pdfs():
    """Create list of files from direct selection"""
    files_output = filedialog.askopenfilenames(
        title="Select file",
        filetypes=(("PDF files", "*.pdf"), ("all files", "*.*"))
    )
    if files_output:
        sad = pathlib.Path(files_output[0])
        local_path = str(sad.parent)
        dir_loop(files_output, local_path)


def calc_avg():
    """Query for weighted price averages and write to Google Sheet"""
    sql_avg = """SELECT itm, item, SUM(qty), SUM(QTY * price) / SUM(qty)
                 FROM items
                 WHERE credit = 0
                 GROUP BY itm;"""
    rows = db.fetch_all(sql_avg)

    credentials = ServiceAccountCredentials.from_json_keyfile_name(
        'YOUR_FILE.json', GOOGLE_SCOPE)
    gc = gspread.authorize(credentials)
    avg_sheet = gc.open('WORKBOOK_NAME').worksheet("WORKSHEET_NAME")

    row_end = str(len(rows) + 1)
    ranges = {
        'itm': avg_sheet.range('A2:A' + row_end),
        'item': avg_sheet.range('B2:B' + row_end),
        'count': avg_sheet.range('C2:C' + row_end),
        'avg': avg_sheet.range('D2:D' + row_end)
    }

    for row, cells in zip(rows, zip(*ranges.values())):
        for cell, value in zip(cells, row):
            cell.value = value

    for range_cells in ranges.values():
        avg_sheet.update_cells(range_cells)

    print("Google Sheet Updated")


def dir_loop(files_output, local_path):
    if db is None or db.cursor is None:
        raise RuntimeError("Database connection not established")

    query_builder = SQLQueryBuilder()
    string_cleaner = StringCleaner()
    total_items = 0
    freight_invoice = ''

    try:
        for pdf in files_output:
            pdf_processor = PDFProcessor(pdf)
            long_list, short_list, invoice_info = pdf_processor.process_pdf()
            invoice_no, invoice_date, year, month, day = invoice_info
            file_name = pdf_processor.file_name

            # Process freight
            frt_index = next((i + 1 for i, line in enumerate(long_list)
                            if 'Freight' in line), 0)

            # Process line items
            name_check = [1]
            markers = [i for i, line in enumerate(short_list)
                      if represents_int(line) and (i - name_check[-1] != 1)]
            name_check.extend(markers)

            for x, y in zip(markers[:-1], markers[1:]):
                cur_list = short_list[x:y]
                qty, itm, prc, price, item_type, price_total_raw = define_bunch(cur_list)

                price_total = string_cleaner.clean_price(price_total_raw)
                taxable = 1 if 'T' in cur_list[3] else 0

                if "Credit Invoice" in long_list[3]:
                    price = negative_val(price)
                    price_total = negative_val(price_total)

                name_list = list(filter(None, cur_list[4].split('  ')))
                item = string_cleaner.clean_item_name(name_list[0])

                total_items += 1
                query = query_builder.build_item_query(
                    invoice_no, invoice_date, year, month, day, qty, itm, item,
                    item_type, price, price_total, taxable, file_name,
                    desc=cur_list[5] if y - x == 6 else None
                )
                db.execute(query)

            if "Freight" in long_list and file_name != freight_invoice:
                freight_invoice = file_name
                freight_price = string_cleaner.clean_price(long_list[frt_index].strip())
                freight_query = query_builder.build_freight_query(
                    invoice_no, invoice_date, year, month, day, freight_price, file_name
                )
                db.execute(freight_query)

        print(f'Processed {total_items} items')
    except Exception as e:
        print(f'Error processing files: {e}')
        raise


def main():
    root = Tk()
    app = InvoiceProcessorGUI(root)
    root.mainloop()

    if db is not None:
        close_connection()


if __name__ == "__main__":
    main()