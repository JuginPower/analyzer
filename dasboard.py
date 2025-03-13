from pathlib import Path
import os
from funcs import choose_theory


BASE_DIR = Path(__file__).resolve().parent.parent
path_database = os.path.join(BASE_DIR, "finance.sqlite3")

theory_name = choose_theory(path_database)

print("Programm stops now!")
