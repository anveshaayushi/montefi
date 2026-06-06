# database.py — DB connection + table creation
import peewee as pw
from config import DB_PATH

db = pw.SqliteDatabase(DB_PATH)


class Portfolio(pw.Model):
    import datetime
    id         = pw.AutoField()
    name       = pw.CharField(max_length=100)
    session_id = pw.CharField(max_length=100, default="default")
    created_at = pw.DateTimeField()
    updated_at = pw.DateTimeField()

    class Meta:
        database   = db
        table_name = "portfolios"


class Holding(pw.Model):
    id        = pw.AutoField()
    portfolio = pw.ForeignKeyField(Portfolio, backref="holdings", on_delete="CASCADE")
    ticker    = pw.CharField(max_length=10)
    weight    = pw.FloatField()

    class Meta:
        database   = db
        table_name = "holdings"


class SimulationResult(pw.Model):
    id         = pw.AutoField()
    portfolio  = pw.ForeignKeyField(Portfolio, backref="simulations", on_delete="CASCADE")

    initial_investment    = pw.FloatField()
    years                 = pw.IntegerField()
    simulation_count      = pw.IntegerField()
    expected_value        = pw.FloatField()
    expected_return_pct   = pw.FloatField(null=True)
    sharpe_ratio          = pw.FloatField(null=True)
    var_95_pct            = pw.FloatField(null=True)
    var_99_pct            = pw.FloatField(null=True)
    max_drawdown_pct      = pw.FloatField(null=True)
    beta                  = pw.FloatField(null=True)
    prob_profit_pct       = pw.FloatField(null=True)
    annualised_return_pct = pw.FloatField(null=True)

    latency_data_fetch_ms  = pw.FloatField(null=True)
    latency_simulation_ms  = pw.FloatField(null=True)
    latency_metrics_ms     = pw.FloatField(null=True)
    latency_ai_ms          = pw.FloatField(null=True)
    latency_total_ms       = pw.FloatField(null=True)

    confidence_intervals_json = pw.TextField(null=True)
    ai_analysis               = pw.TextField(null=True)
    run_at                    = pw.DateTimeField()

    class Meta:
        database   = db
        table_name = "simulation_results"


def connect_db():
    import datetime
    db.connect(reuse_if_open=True)
    db.create_tables([Portfolio, Holding, SimulationResult], safe=True)
    print(f"[DB] Connected: {DB_PATH}")