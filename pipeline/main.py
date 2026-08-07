from config.config import DATABASE_NAME, GPS_FILE, INVOICE_FILE
from config.constants import GPS_RAW, INVOICE_RAW

from readers.gps_reader import GPSReader
from readers.invoice_reader import InvoiceReader

from database.mongo import MongoDB
from database.save import save_to_collection


def main():
    print("Connecting to MongoDB...", flush=True)

    mongo = MongoDB()

    gps_collection = mongo.get_collection(GPS_RAW)
    invoice_collection = mongo.get_collection(INVOICE_RAW)

    print("Connected to MongoDB", flush=True)
    print(f"Database: {DATABASE_NAME}", flush=True)
    print(
        f"Collections: {gps_collection.name}, {invoice_collection.name}",
        flush=True,
    )
    print("Reading GPS...", flush=True)

    gps_records = GPSReader(GPS_FILE).read()

    print(f"Loaded {len(gps_records)} GPS records", flush=True)

    save_to_collection(gps_collection, gps_records)

    print("GPS saved to MongoDB", flush=True)

    print("Reading Invoice...", flush=True)

    invoices = InvoiceReader(INVOICE_FILE).read()

    print(f"Loaded {len(invoices)} invoices", flush=True)

    save_to_collection(invoice_collection, invoices)

    print("Invoices saved to MongoDB", flush=True)


if __name__ == "__main__":
    main()
