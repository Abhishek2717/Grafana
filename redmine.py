import datetime
from re import S
import time
import os
from sys import exit
import requests

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

    def __init__(self, target):
        self._target = target

    def collect(self):
        start = time.time()
        self._setup_empty_prometheus_metrics()
        # Request data from Redmine
        self._request_data()

        for status in self.apimetrics:
            for metric in self._prometheus_metrics.values():
                yield metric

        duration = time.time() - start
        COLLECTION_TIME.observe(duration)

    def _request_data(self):
        # Request exactly the information we need from Redmine
        redmine = Redmine(self._target)
        _date = datetime.datetime.now()
        _datetimestamp = time.mktime(_date.timetuple())

        for issue in redmine.issue.filter(duedate=_date):
            self._prometheus_metrics['duedate'].add_metric([issue.project.name, str(issue.id), issue.status.name, issue.tracker.name, issue.priority.name, issue.assigned_to.name, issue.subject], _datetimestamp)
       
        for project in redmine.project.all():
            self._prometheus_metrics['total_open_projects'].add_metric([str(project.id),project.name,str(project.status),str(project.issues),str(project.news)], _datetimestamp)
            
            open = len(redmine.issue.filter(status_id=1))
            self._prometheus_metrics['openissues'].add_metric([project.name,str(project.id),str(project.status),str(project.issues),str(project.news)], open)
            
            resolved = len(redmine.issue.filter(status_id='open'))
            self._prometheus_metrics['resolvedissues'].add_metric([project.name,str(project.id),str(project.status),str(project.issues),str(project.news)], resolved)
            
            closed = len(redmine.issue.filter(status_id='closed'))
            self._prometheus_metrics['closedissues'].add_metric([project.name,str(project.id),str(project.status),str(project.issues),str(project.news)], closed)
            
            onhold = len(redmine.issue.filter(status_id=1))
            self._prometheus_metrics['onholdissues'].add_metric([project.name,str(project.id),str(project.status),str(project.issues),str(project.news)], onhold)
            
            inprogress = len(redmine.issue.filter(status_id=1))
            self._prometheus_metrics['inprogressissues'].add_metric([project.name,str(project.id),str(project.status),str(project.issues),str(project.news)], inprogress)
            
            feedback = len(redmine.issue.filter(status_id=1))
            self._prometheus_metrics['feedbackissues'].add_metric([project.name,str(project.id),str(project.status),str(project.issues),str(project.news)], feedback)

        

    def _setup_empty_prometheus_metrics(self):
        # The metrics we want to export.
        self._prometheus_metrics = {}
        self._prometheus_metrics['total_open_issues'] = GaugeMetricFamily('Redmine_Project_Issue','Redmine Project Total Issue Open',
                                                                labels=["projectname", "issueid", "status", "tracker","priority", "author", "user"])
        self._prometheus_metrics['total_open_projects'] = GaugeMetricFamily('Redmine_Projects','Redmine Total Project',
                                                                labels=['id','name','status','issues','news'])
        self._prometheus_metrics['openissues'] = GaugeMetricFamily('Redmine_Openissues','Redmine OpenIsuues',
                                                                labels=['projectname','id','status','issues','news'])
        self._prometheus_metrics['resolvedissues'] = GaugeMetricFamily('Redmine_Resolvedissues','Redmine ResolveIsuues',
                                                                labels=['projectname','id','status','issues','news'])
        self._prometheus_metrics['closedissues'] = GaugeMetricFamily('Redmine_Closedissues','Redmine ClosedIsuues',
                                                                labels=['projectname','id','status','issues','news'])
        self._prometheus_metrics['onholdissues'] = GaugeMetricFamily('Redmine_Onholdissues','Redmine OnHoldIssues',
                                                                labels=['projectname','id','status','issues','news'])
        self._prometheus_metrics['inprogressissues'] = GaugeMetricFamily('Redmine_Inprogressissues','Redmine InProgressIssues',
                                                                labels=['projectname','id','status','issues','news'])
        self._prometheus_metrics['feedbackissues'] = GaugeMetricFamily('Redmine_Feedbackissues','Redmine FeedBackIssues',
                                                                labels=['projectname','id','status','issues','news'])
        self._prometheus_metrics['duedate'] = GaugeMetricFamily('Redmine_Duedate','Redmine DueDate',
                                                                labels=['projectname','id','status','tracker','priority','assignee','subject'])
def main():
    try:
        redmine = "https://kore.koders.in/"
        REGISTRY.register(RedmineCollector(redmine))
        start_http_server(9900)
        print("Polling {}. Serving at port: {}".format(redmine, 9900))
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print(" Interrupted")
        exit(0)


if __name__ == "__main__":
    main()
