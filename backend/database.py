# database.py — DB connection + table creation
import peewee as pw
from config import DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT

db = pw.PostgresqlDatabase(
    DB_NAME,
    user=DB_USER,
    password=DB_PASSWORD,
    host=DB_HOST,
    port=DB_PORT,
)


def connect_db():
    from portfolio import Portfolio
    from holding import Holding
    from simulation_result import SimulationResult
    db.connect(reuse_if_open=True)
    db.create_tables([Portfolio, Holding, SimulationResult], safe=True)
    print(f"[DB] Connected to Postgres: {DB_NAME}@{DB_HOST}:{DB_PORT}")