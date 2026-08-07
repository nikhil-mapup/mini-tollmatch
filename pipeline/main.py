from config.config import GPS_FILE
from config.config import INVOICE_FILE
from readers.gps_reader import GPSReader
from readers.invoice_reader import InvoiceReader

def main():
    gps = GPSReader(GPS_FILE).read()
    invoices = InvoiceReader(INVOICE_FILE).read()
    
    print(f"GPS Records : {len(gps)}")
    print(f"Invoices : {len(invoices)}")
    
if __name__ == "__main__":
    main()