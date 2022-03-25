
from github import Github
g = Github('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')

repo = g.get_repo("Arriven/db1000n")

open_issues = repo.get_issues(state='open')
for issue in open_issues:
     print(issue)


