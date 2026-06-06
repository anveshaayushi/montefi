# models/simulation_result.py
import datetime
import peewee as pw
from database import db
from portfolio import Portfolio


class SimulationResult(pw.Model):
    id         = pw.AutoField()
    portfolio  = pw.ForeignKeyField(Portfolio, backref="simulations", on_delete="CASCADE")

    # inputs
    initial_investment = pw.FloatField()
    years              = pw.IntegerField()
    simulation_count   = pw.IntegerField()

    # outputs
    expected_value        = pw.FloatField()
    expected_return_pct   = pw.FloatField(null=True)
    sharpe_ratio          = pw.FloatField(null=True)
    var_95_pct            = pw.FloatField(null=True)
    var_99_pct            = pw.FloatField(null=True)
    max_drawdown_pct      = pw.FloatField(null=True)
    beta                  = pw.FloatField(null=True)
    prob_profit_pct       = pw.FloatField(null=True)
    annualised_return_pct = pw.FloatField(null=True)

    # latency (ms) for each stage — new field
    latency_data_fetch_ms  = pw.FloatField(null=True)
    latency_simulation_ms  = pw.FloatField(null=True)
    latency_metrics_ms     = pw.FloatField(null=True)
    latency_ai_ms          = pw.FloatField(null=True)
    latency_total_ms       = pw.FloatField(null=True)

    confidence_intervals_json = pw.TextField(null=True)
    ai_analysis               = pw.TextField(null=True)
    run_at                    = pw.DateTimeField(default=datetime.datetime.utcnow)

    class Meta:
        database   = db
        table_name = "simulation_results"