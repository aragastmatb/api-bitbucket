import re
import bitbucket
from runpy import run_path
import os
from environment import items
import argparse
from datetime import datetime as dt

#-------------------!!Init Bitbucket!!----------------------------#

def load_module(dir):
    bitbucket_py = "bitbucket.py"
    bitbucket_module = run_path(os.path.join(dir,bitbucket_py))
    BitBucket = bitbucket_module['BitBucket']

    return BitBucket

def connect_bitbucket(user, password):
    url = items['auth']['url']

    try:
        nb_dir = os.path.split(os.getcwd())[0]
        BitBucket = load_module(nb_dir)
    except Exception:
        nb_dir = os.getcwd()
        BitBucket = load_module(nb_dir)
    try:
        bitbucket_ci = BitBucket(url, user, password, gitPath='tmp', is_windows=True)
    except Exception:
        print('Invalid login or password, please, check and try again')
        exit()
    return bitbucket_ci

#-------------------!!Init Bitbucket!!----------------------------#

def get_bb_ci_projects(bitbucket_ci):
    res, projects = bitbucket_ci.get_projects()
    bb_ci_projects_key = [x['key'].lower() for x in projects['values']]
    return bb_ci_projects_key

def main(user, password, new_user):
    #-------------------!!Main Variable!!----------------------------#
    bitbucket_ci = connect_bitbucket(user, password)
    project_repos_restrict = {}
    all_project_key = get_bb_ci_projects(bitbucket_ci)
    count_project_permission = 0
    count_repos_permission = 0
    count_project = len(all_project_key)
    count_repos = 0
    try:
        bitbucket_ci.get_user_info(new_user)
    except Exception:
        print('Invalid new user, please, check and try again')
        exit()

    #-------------------!!Main!!----------------------------#

    print('Всего проектов: {}'.format(str(count_project)))
    for project in all_project_key:
        all_repos = bitbucket_ci.get_repos(project)
        count_repos += len(all_repos)
        project_restrict_list = bitbucket_ci.get_project_restrictions(project)
        for project_restrict in project_restrict_list[1]['values']:
            count_project_permission += 1
            if project_restrict['type'] != 'fast-forward-only':
                current_project_keys = []
                for current in project_restrict['accessKeys']:
                    current_project_keys.append(current['key']['id'])
                current_project_groups = []
                for current in project_restrict['groups']:
                    current_project_groups.append(current)
                new_project_users = []
                for current in project_restrict['users']:
                    if current['name'] != 'simplelogin':
                        try:
                            bitbucket_ci.get_user_info(current['name'])
                            new_project_users.append(current['name'])
                        except Exception:
                            with open('error_restriction.log', 'a') as log_file:
                                log_file.write('WARNING: Cannot get {} - reason: inactive\n'.format(current['name']))
                new_project_users.append(new_user)
                new_project_users.remove(new_user)
                new_project_restrict = {"types": project_restrict['type'], "matcher": {"id": project_restrict['matcher']['id'], "displayId": project_restrict['matcher']['displayId'], "type": project_restrict['matcher']['type'], "active": project_restrict['matcher']['active']}, "users": new_project_users, "groups": current_project_groups, "accessKeys": current_project_keys}
                try:
                    project_change = bitbucket_ci.set_project_restrictions(project, restrict = new_project_restrict)
                except Exception as e:
                    with open('error_restriction.log', 'a') as log_file:
                        log_file.write(str(e) + '\n')
        for repos in all_repos[1]['values']:
            try:
                repos_restrict_list = bitbucket_ci.get_restrictions(project, repos['name'])
                if repos_restrict_list[0]['status_code'] == 200 and repos_restrict_list[1]['size'] > 0:
                    for repos_restrict in repos_restrict_list[1]['values']:
                        count_repos_permission += 1
                        if (repos_restrict['scope']['type'] != 'PROJECT') and (repos_restrict['type'] != 'fast-forward-only'):
                            current_keys = []
                            for current in repos_restrict['accessKeys']:
                                current_keys.append(current['key']['id'])
                            current_groups = []
                            for current in repos_restrict['groups']:
                                current_groups.append(current)
                            new_users = []
                            for current in repos_restrict['users']:
                                if current['name'] != 'Metlyakov1-AA':
                                    try:
                                        bitbucket_ci.get_user_info(current['name'])
                                        new_users.append(current['name'])
                                    except Exception:
                                        with open('error_restriction.log', 'a') as log_file:
                                            log_file.write('WARNING: Cannot get {} - reason: inactive\n'.format(current['name']))
                            new_users.append(new_user)
                            new_users.remove(new_user)
                            new_restrict = {"types": repos_restrict['type'], "matcher": {"id": repos_restrict['matcher']['id'], "displayId": repos_restrict['matcher']['displayId'], "type": repos_restrict['matcher']['type'], "active": repos_restrict['matcher']['active']}, "users": new_users, "groups": current_groups, "accessKeys": current_keys}
                            try:
                                repos_change = bitbucket_ci.set_restrictions(project, repos['name'], restrict = new_restrict)
                            except Exception as e:
                                with open('error_restriction.log', 'a') as log_file:
                                    log_file.write(str(e) + '\n')
            except Exception as e:
                with open('error_restriction.log', 'a') as log_file:
                    log_file.write(str(e) + '\n')
    return count_project_permission, count_repos_permission, count_project, count_repos

def check_input(param, type):
    escape_char = ('\n', '\t', ' ', '\r', '\a', '\f', '\v', '\b')
    for char in escape_char:
        param = param.replace(char, '')
    if len(param) == 0:
        print("Your {type} doesn't correct".format(type = type))
        exit()
    else:
        return param

parser = argparse.ArgumentParser()
parser.add_argument(
    'login',  type=str, help='Stash admin username')
parser.add_argument(
    'password', type=str, help='Stash admin password')
parser.add_argument(
    '-n', '--new', type=str, help='User login what you need to push into all branch permission', required = True)
args = parser.parse_args()
user = args.login
user = check_input(user, 'login')
password = args.password
password = check_input(password, 'password')
new_user = args.new
new_user = check_input(new_user, 'new user')
start_time = dt.now()
print('Время начала: {}'.format(str(dt.now())))
count_all = main(user, password, new_user)
finish_time = dt.now()
print('Всего ограничений на уровне проекта: {}'.format(str(count_all[0])))
print('Всего репозиториев: {}'.format(str(count_all[3])))
print('Всего ограничений на уровне репозитория: {}'.format(str(count_all[1])))
print('Время окончания: {}'.format(str(dt.now())))
delta_time = finish_time - start_time
print('Всего затрачено: {}'.format(str(delta_time)))
print('В среднем на проект: {}'. format(str(delta_time/count_all[2])))
print('В среднем на репозиторий: {}'. format(str(delta_time/count_all[3])))
print('В среднем на один Branch Permission: {}'. format(str(delta_time/(count_all[0] + count_all[1]))))
