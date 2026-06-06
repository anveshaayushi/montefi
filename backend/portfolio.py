# models/portfolio.py
import datetime
import peewee as pw
from database import db


class Portfolio(pw.Model):
    id         = pw.AutoField()
    name       = pw.CharField(max_length=100)
    session_id = pw.CharField(max_length=100, default="default")
    created_at = pw.DateTimeField(default=datetime.datetime.utcnow)
    updated_at = pw.DateTimeField(default=datetime.datetime.utcnow)

    class Meta:
        database   = db
        table_name = "portfolios"