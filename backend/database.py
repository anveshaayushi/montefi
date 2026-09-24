# database.py — DB connection + table creation
import peewee as pw
from config import DB_PATH

db = pw.SqliteDatabase(DB_PATH)


def connect_db():
    from portfolio import Portfolio
    from holding import Holding
    from simulation_result import SimulationResult
    db.connect(reuse_if_open=True)
    db.create_tables([Portfolio, Holding, SimulationResult], safe=True)
    print(f"[DB] Connected: {DB_PATH}")