import datetime
import time
import os
from sys import exit
from prometheus_client import start_http_server, Summary
from prometheus_client.core import GaugeMetricFamily, REGISTRY
from redminelib import Redmine
from redminelib.exceptions import ResourceAttrError
from dotenv import load_dotenv

load_dotenv()

COLLECTION_TIME = Summary('redmine_collector_collect_seconds', 'Time spent to collect metrics from Redmine')


class RedmineCollector(object):
    apimetrics = ["redmine_project_last7days_count"]

    def __init__(self, target, api):
        self._target = target.rstrip("/")
        self.api = api

    def collect(self):
        start = time.time()
        self._setup_empty_prometheus_metrics()
        # Request data from Redmine
        jobs = self._request_data()

        for status in self.apimetrics:
            for metric in self._prometheus_metrics.values():
                yield metric

        duration = time.time() - start
        COLLECTION_TIME.observe(duration)

    def _request_data(self):
        # Request exactly the information we need from Redmine
        redmine = Redmine(self._target, key=self.api)

        _date = datetime.datetime.now()
        _datetimestamp = time.mktime(_date.timetuple())

        week = []
        for i in range(0, 7):
            week.append(((datetime.datetime.now() - datetime.timedelta(days=i)).date()))

        for day in week:
            time_entries = redmine.time_entry.filter(spent_on=day)
            for entry in time_entries:
                try:
                    self._prometheus_metrics['spent7days'].add_metric([entry.project.name, str(entry.issue.id), str(entry.user.name), entry.activity.name, str(entry.hours), entry.spent_on.strftime('%d/%m/%Y')], str(entry.id))
                except ResourceAttrError:
                    self._prometheus_metrics['spent7days'].add_metric([entry.project.name, "None", str(entry.user.name), entry.activity.name, str(entry.hours), entry.spent_on.strftime('%d/%m/%Y')], str(entry.id))

    def _setup_empty_prometheus_metrics(self):
        # The metrics we want to export.
        self._prometheus_metrics = {}
        self._prometheus_metrics['spent7days'] = GaugeMetricFamily('redmine_project_issue_spenttime_last_week_hours',
                                                                 'Redmine Project SpentTime Duration Hours Of Last Week',
                                                                 labels=["project name", "issue", "user", "activity", "hours", "day"])

def main():
    try:
        redmine = os.getenv('URL')
        api = os.getenv('API')
        port = int(os.getenv('PORT'))
        REGISTRY.register(RedmineCollector(redmine, api))
        start_http_server(port)
        print("Polling {}. Serving at port: {}".format(redmine, port))
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print(" Interrupted")
        exit(0)


if __name__ == "__main__":
    main()
