from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent.parent

DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output"

GPS_FILE = DATA_DIR / "Fleet_A_gps.parquet"
INVOICE_FILE = DATA_DIR / "FleetA_invoices.csv"

MONGO_URI = os.getenv("MONGO_URI")
DATABASE_NAME = os.getenv("DATABASE_NAME", "tollmatch")