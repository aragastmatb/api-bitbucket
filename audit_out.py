from bitbucket import BitBucket
import argparse
from datetime import datetime as dt

def check_input(param, types):
    escape_char = ('\n', '\t', ' ', '\r', '\a', '\f', '\v', '\b')
    for char in escape_char:
        param = param.replace(char, '')
    if len(param) == 0:
        print("Your {type} doesn't correct".format(type = types))
        exit()
    else:
        return param

parser = argparse.ArgumentParser()
parser.add_argument(
    'user',  type=str, help='Stash admin username')
parser.add_argument(
    'password', type=str, help='Stash admin password')
parser.add_argument(
    'url', type=str, help='Full URL for sonar'
)
args = parser.parse_args()
user = args.user
user = check_input(user, 'login')
password = args.password
password = check_input(password, 'password')
url = args.url
url = check_input(url, 'url')
print(str(dt.now()))
bb = BitBucket(url, user, password)

projects = bb.get_project_ids()

for project in projects:
    try:
        repos = bb.get_repo_ids(project)
    except Exception:
        repos = []
    try:
        project_permissions = bb.get_permissions_users_in_project(project)[1]['values']
    except Exception:
        project_permissions = []
    for permission in project_permissions:
        if permission['permission'] == 'PROJECT_ADMIN':
            if 'out-' in permission['user']['name'].lower():
                with open('audit_result.txt' , 'a') as result_file:
                    try:
                        result_file.write(project + ':' + permission['user']['name'] + ';' + permission['user']['emailAddress'] + '\n')
                    except Exception:
                        result_file.write(project + ':' + permission['user']['name'] + '\n')
                result = bb.delete_permission_user_in_project(project, permission['user']['name'])
                try:
                    result = bb.create_permission_user_in_project(project,'PROJECT_WRITE',permission['user']['name'])
                except:
                    result = ''
    for repo in repos:
        try:
            repos_repmissions = bb.get_permissions(project, repo)[1]['values']
        except Exception:
            repos_repmissions = []
        for permission in repos_repmissions:
            if permission['permission'] == 'REPOS_ADMIN':
                if 'out-' in permission['user']['name'].lower():
                    with open('audit_result.txt', 'a') as result_file:
                        try:
                            result_file.write(project + ':' + repo + ':' + permission['user']['name'] + ';' + permission['user']['emailAddress'] + '\n')
                        except Exception:
                            result_file.write(project + ':' + repo + ':' + permission['user']['name'] + '\n')
                    result = bb.delete_permission_user(project, repo, permission['user']['name'])
                    result = bb.create_permission_user(project, repo, {'name':permission['user']['name'], 'permission':'REPO_WRITE'})
print(str(dt.now()))
