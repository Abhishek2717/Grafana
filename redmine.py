import datetime
import time
import os
from sys import exit
from prometheus_client import start_http_server, Summary
from prometheus_client.core import GaugeMetricFamily, REGISTRY
from redminelib import Redmine
from dotenv import load_dotenv

load_dotenv()

COLLECTION_TIME = Summary('redmine_collector_collect_seconds', 'Time spent to collect metrics from Redmine')


class RedmineCollector(object):
    apimetrics = ["redmine_project_open_issues_total_count", "redmine_project_closed_issues_total_count",
                  "redmine_project_resolved_issues_total_count", "redmine_project_onhold_issues_total_count",
                  "redmine_project_inprogress_issues_total_count", "redmine_project_feedback_issues_total_count",
                  "redmine_project_activeusers_count", "redmine_project_issue_due_date",
                  ]

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

        _date = datetime.datetime.now().date()
        _datetimestamp = time.mktime(_date.timetuple())
        self._prometheus_metrics['todaydate'].add_metric([_date.strftime("%m/%d/%Y")], _datetimestamp)

        count = len(redmine.user.all())
        self._prometheus_metrics['activeusers'].add_metric(['activeusers'], count)

        for project in redmine.project.all():
            count = len(redmine.issue.filter(status_id='open', project_id=project.id))
            self._prometheus_metrics['openissues'].add_metric([project.name], count)
            count = len(redmine.issue.filter(status_id=3, project_id=project.id))
            self._prometheus_metrics['resolvedissues'].add_metric([project.name], count)
            count = len(redmine.issue.filter(status_id='closed', project_id=project.id))
            self._prometheus_metrics['closedissues'].add_metric([project.name], count)
            count = len(redmine.issue.filter(status_id=10, project_id=project.id))
            self._prometheus_metrics['onholdissues'].add_metric([project.name], count)
            count = len(redmine.issue.filter(status_id=2, project_id=project.id))
            self._prometheus_metrics['inprogressissues'].add_metric([project.name], count)
            count = len(redmine.issue.filter(status_id=4, project_id=project.id))
            self._prometheus_metrics['feedbackissues'].add_metric([project.name], count)

        for issue in redmine.issue.all(due_date=_date):
            self._prometheus_metrics['duedate'].add_metric([issue.project.name, str(issue.id), issue.status.name, issue.tracker.name, issue.priority.name, _date.strftime('%d/%m/%Y'), issue.author.name, issue.assigned_to.name], _datetimestamp)

    def _setup_empty_prometheus_metrics(self):
        # The metrics we want to export.
        self._prometheus_metrics = {}

        # snake_case = re.sub('([A-Z])', '_\\1', status).lower()
        self._prometheus_metrics['activeusers'] = GaugeMetricFamily('active_users',
                                                                  'Shows total active users',
                                                                  labels=["users"])

        self._prometheus_metrics['todaydate'] = GaugeMetricFamily('redmine_today_date',
                                                                   'Shows todays date',
                                                                   labels=["date"])
        self._prometheus_metrics['openissues'] = GaugeMetricFamily('redmine_project_open_issues_total_count',
                                                                   'Redmine Project Open Issues Count',
                                                                   labels=["projectname"])
        self._prometheus_metrics['resolvedissues'] = GaugeMetricFamily('redmine_project_resolved_issues_total_count',
                                                                     'Redmine Project Resolved Issues Count',
                                                                     labels=["projectname"])
        self._prometheus_metrics['onholdissues'] = GaugeMetricFamily('redmine_project_onhold_issues_total_count',
                                                                       'Redmine Project On hold Issues Count',
                                                                       labels=["projectname"])
        self._prometheus_metrics['feedbackissues'] = GaugeMetricFamily('redmine_project_feedback_issues_total_count',
                                                                     'Redmine Project Feedback Issues Count',
                                                                     labels=["projectname"])
        self._prometheus_metrics['inprogressissues'] = GaugeMetricFamily('redmine_project_inprogress_issues_total_count',
                                                                       'Redmine Project In-Progress Issues Count',
                                                                       labels=["projectname"])
        self._prometheus_metrics['closedissues'] = GaugeMetricFamily('redmine_project_closed_issues_total_count',
                                                                     'Redmine Project Closed Issues Count',
                                                                     labels=["projectname"])
        self._prometheus_metrics['duedate'] = GaugeMetricFamily('redmine_project_issue_due_date',
                                                                'Redmine Due by Today',
                                                                labels=["projectname", "issueid", "status", "tracker",
                                                                        "priority", "duedate", "author", "user"])


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
