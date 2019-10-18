# PDF Invoice Scraper
Scrape text-based PDF invoices, insert lines items into SQLite database, and generate summary reports.

## Author
**John Carlee** - [Email me](mailto:JCarlee@gmail.com)

I am 9 year veteran in the Geographic Information Science and Cartography space.

## Motivation
After seeing a friend struggle with handling hundreds of paper invoices, I wanted to relieve the majority of work.

## Dependencies
* Python 3
* PyPDF2
* sqlite3
* re
* os
* tkinter
* gspread

```
pip install PyPDF2
pip install gspread
```

## How it Works
* Loop through a directory of PDF invoices
* Extract line items, modify with specific handlers
* Insert line items into SQlite database
* Commit insert statements

_This specialized script works specifically for Krueger Wholesale invoices created for daffodil*parker in Madison, WI._
