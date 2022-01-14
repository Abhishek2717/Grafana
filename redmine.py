import datetime
import time
import os
from sys import exit

import redminelib.exceptions
from prometheus_client import start_http_server, Summary
from prometheus_client.core import GaugeMetricFamily, REGISTRY
from redminelib import Redmine
from dotenv import load_dotenv

load_dotenv()

COLLECTION_TIME = Summary('redmine_collector_collect_seconds', 'Time spent to collect metrics from Redmine')


class RedmineCollector(object):
    # The build apimetrics we want to export about.
    apimetrics = ["redmine_issue_open"]

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

        for issue in redmine.issue.all(status_id='open'):
            try:
                self._prometheus_metrics['total_open_issues'].add_metric([issue.project.name, str(issue.id), issue.status.name, issue.tracker.name, issue.priority.name, issue.author.name, issue.assigned_to.name], _datetimestamp)
            except redminelib.exceptions.ResourceAttrError:
                self._prometheus_metrics['total_open_issues'].add_metric([issue.project.name, str(issue.id), "None", "None", "None", "None", "None"], _datetimestamp)


    def _setup_empty_prometheus_metrics(self):
        # The metrics we want to export.
        self._prometheus_metrics = {}
        self._prometheus_metrics['total_open_issues'] = GaugeMetricFamily('redmine_project_issue_due_date',
                                                                'Redmine Project Total Issue Open',
                                                                labels=["projectname", "issueid", "status", "tracker",
                                                                        "priority", "author", "user"])


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
