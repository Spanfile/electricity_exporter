from datetime import datetime

import requests
from pytz import utc
from prometheus_client import make_wsgi_app, Gauge
from flask import Flask
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from apscheduler.schedulers.background import BackgroundScheduler


class ElectricityTracker:
    prices = []

    def __init__(self, gauge: Gauge):
        self.gauge = gauge

    def fetch_prices(self):
        resp = requests.get(
            "https://api.porssisahko.net/v1/latest-prices.json", timeout=10
        )

        latest_prices = resp.json()
        self.prices = latest_prices["prices"]

        print("prices updated")

    def update_current_price(self):
        # dates in the price JSON are in UTC
        now = datetime.now()
        utc_now = datetime.utcnow().replace(tzinfo=utc)

        current_price = next(
            elem["price"]
            for elem in self.prices
            if datetime.fromisoformat(elem["startDate"])
            <= utc_now
            < datetime.fromisoformat(elem["endDate"])
        )

        self.gauge.set(current_price)
        print(now, ": price for hour", now.hour, ":", current_price)


elec_gauge = Gauge("electricity_price", "Current electricity price")
tracker = ElectricityTracker(elec_gauge)

tracker.fetch_prices()
tracker.update_current_price()

scheduler = BackgroundScheduler()
scheduler.add_job(tracker.fetch_prices, "cron", hour="09-23/12", minute="0")
scheduler.add_job(tracker.update_current_price, "cron", hour="*", minute="0")
# scheduler.add_job(tracker.update_price, "interval", seconds=5)
scheduler.start()

app = Flask(__name__)
app.wsgi_app = DispatcherMiddleware(app.wsgi_app, {"/metrics": make_wsgi_app()})
