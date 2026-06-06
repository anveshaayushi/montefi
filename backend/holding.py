# models/holding.py
import peewee as pw
from database import db
from portfolio import Portfolio


class Holding(pw.Model):
    id        = pw.AutoField()
    portfolio = pw.ForeignKeyField(Portfolio, backref="holdings", on_delete="CASCADE")
    ticker    = pw.CharField(max_length=10)
    weight    = pw.FloatField()   # 0.0–1.0; all holdings in a portfolio must sum to 1.0

    class Meta:
        database   = db
        table_name = "holdings"