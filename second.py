from github import Github
g = Github('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')
username = input("Enter user name to display repos: ")
user = g.get_user(username) 
repos = user.get_repos()
i = 0
list_of_repos = []
for repo in user.get_repos():
        list_of_repos.append(repo.name)
        print(list_of_repos[i])
        i=i+1




# Pull request
# Commits, Description

