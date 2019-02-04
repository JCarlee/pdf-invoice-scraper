import PyPDF2

pdfFileObj = open("C:\\Users\\jcarl\\Desktop\\IN490924019.pdf", 'rb')
pdfReader = PyPDF2.PdfFileReader(pdfFileObj)
no_of_pages = pdfReader.getNumPages()

for page in range(no_of_pages):
    pageObj = pdfReader.getPage(page)
    print(pageObj.extractText())

pdfFileObj.close()
