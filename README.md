# PDF Invoice Scraper
Scrape text-based PDF invoices, insert lines items into SQLite database, and generate summary reports.

## Motivation
After seeing a florist friend struggle with handling hundreds of paper invoices, I wanted to relieve the majority of work.

## Dependencies
* Python 3
* PyPDF2
* sqlite3
* re
* os

```
pip install PyPDF2
```

## How it Works
* Loop through a directory of PDF invoices
* Extract line items, modify with specific handlers
* Insert line items into SQlite database
* Commit insert statements

_This specialized script works specifically for Krueger Wholesale invoices created for daffodil*parker in Madison, WI._
## Author

* **John Carlee** - JCarlee@gmail.com
