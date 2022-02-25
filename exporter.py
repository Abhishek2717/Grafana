import datetime
import time
import os
from sys import exit

from prometheus_client import start_http_server, Summary
from prometheus_client.core import GaugeMetricFamily, REGISTRY
from github import Github
from dotenv import load_dotenv

access_token = Github("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")
login  = access_token
user  = login.get_user()

load_dotenv()

COLLECTION_TIME = Summary('Github_collector_collect_seconds', 'Time spent to collect metrics from Github')

class GithubCollector(object):
    apimetrics = ["github_issues_open"]

    def __init__(self, target):
        self._target = target

    def collect(self):
        start = time.time()
        self._setup_empty_prometheus_metrics()
        self._request_data()

        for status in self.apimetrics:
            for metric in self._prometheus_metrics.values():
                yield metric

        duration = time.time() - start
        COLLECTION_TIME.observe(duration)

    def _request_data(self):
        github = Github(self._target)
        _date = datetime.datetime.now()
        _datetimestamp = time.mktime(_date.timetuple())
        data = user.get_repo('Calculator')
        open_issues = data.get_issues(state="open")
        open_pull = data.get_pulls(state="all")
        open_commits = data.get_commits()
        open_repos = user.get_repos()

        for issue in open_issues:
            self._prometheus_metrics['Total Open Issues'].add_metric([str(issue.id),str(issue.assignee),str(issue.number),issue.comments_url,str(issue.body),str(issue.labels),issue.state], _datetimestamp)
        for pull in open_pull:
            self._prometheus_metrics['Total Open Pull Requests'].add_metric([str(pull.assignee),str(pull.number),pull.comments_url,pull.body], _datetimestamp)
        for commit in open_commits:
            self._prometheus_metrics['Total Commits'].add_metric([str(commit.author),str(commit.commit),str(commit.committer),str(commit.files),str(commit.raw_data),str(commit.stats),commit.url], _datetimestamp)
        for repo in open_repos:
            self._prometheus_metrics['Total Repos'].add_metric([repo.name,str(repo.id),repo.url,repo.clone_url,str(repo.created_at),repo.commits_url,repo.full_name,str(repo.language),str(repo.updated_at),str(repo.watchers)], _datetimestamp)
    
    def _setup_empty_prometheus_metrics(self):
        self._prometheus_metrics = {}
        self._prometheus_metrics['Total Open Issues'] = GaugeMetricFamily('Github_Project_Issues_Open','Github Project Total Issues Open',
                                                                labels=["assignee", "issueid","number","commenyts_url","body","labels","state"])
        self._prometheus_metrics['Total Open Pull Requests'] = GaugeMetricFamily('Github_Project_Pull_Request','Github Project Total Pull Requests Open',
                                                                labels=["assignee", "issueid","number","commenyts_url","body","labels","state"])
        self._prometheus_metrics['Total Commits'] = GaugeMetricFamily('Github_Project_Commits','Github Project Total commits',
                                                                labels=["author","commit","committer","files","raw_data","stats","url"])   
        self._prometheus_metrics['Total Repos'] = GaugeMetricFamily('Github_Project_All_Repos','Github Project Total Repos',
                                                                labels=["name","id","url","clone_url","created_at","commits_url","full_name","language","updated_at","watchers"])                                                                                                              

def main():
    try:
        github = os.getenv('https://github.com/')
        REGISTRY.register(GithubCollector(github))
        start_http_server(9100)
        print("Polling {}. Serving at port: {}".format(github,9100))
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print(" Interrupted")
        exit(0)

if __name__ == "__main__":
    main()