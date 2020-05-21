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

def main(user, password, parser_string, replace_string, replace_tag):
    #-------------------!!Main Variable!!----------------------------#
    bitbucket_ci = connect_bitbucket(user, password)
    project_repos_hook = {}
    all_project_key = get_bb_ci_projects(bitbucket_ci)
    count_repos_hook = 0
    count_project = len(all_project_key)

    #-------------------!!Main!!----------------------------#

    print('Всего проектов: {}'.format(str(count_project)))
    for project in all_project_key:
        try:
            all_repos = bitbucket_ci.get_repos(project)
        except Exception as e:
            with open('error_main.log', 'a') as log_file:
                log_file.write(e)
        repos_hook_list = {}
        for repos in all_repos[1]['values']:
            try:
                repos_hook = bitbucket_ci.get_hooks(project, repos['name'])
            except Exception as e:
                with open('error_main.log', 'a') as log_file:
                    log_file.write(str(e))
            if repos_hook[0]['status_code'] == 200:
                repos_hook_list.update({repos['name']:repos_hook[1]['params']})
        if len(repos_hook_list) > 0:
            count_repos_hook += len(repos_hook_list)
            project_repos_hook.update({project: repos_hook_list})
        for hooked_project in project_repos_hook:
            for hooked_repos in project_repos_hook.get(hooked_project):
                project_repos_hook.get(hooked_project).update({hooked_repos: re.sub(parser_string, replace_string, project_repos_hook.get(hooked_project).get(hooked_repos))})
                if replace_tag:
                    try:
                        bitbucket_ci.set_hooks(hooked_project, hooked_repos, project_repos_hook.get(hooked_project).get(hooked_repos))
                    except Exception as e:
                        with open('error_main.log', 'a') as log_file:
                            log_file.write(str(e))
    return count_repos_hook, count_project

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
    'user',  type=str, help='Stash admin username')
parser.add_argument(
    'password', type=str, help='Stash admin password')
parser.add_argument('regexp', type=str, help='Regular expression for parameter what to be replaced. Exmp:".*--jenkins-job-url=([A-Za-z0-9\-\/_\.:]+)\s*" without quoute or any brakes')
parser.add_argument('replace', type=str, help='String for parameter what used to replaced. Exmp: "jenkins-job-url=https://bitbucket.ru/project/null/\\r\\n" without quote or any brakes')
parser.add_argument('-f', '--force', default = False, action = 'store_true', help='True if need to be replaced')
args = parser.parse_args()
user = args.user
user = check_input(user, 'login')
password = args.password
password = check_input(password, 'password')
parser_string = args.regexp
replace_string = '--' + args.replace
replace_tag = args.force
start_time = dt.now()
print('Время начала: {}'.format(str(dt.now())))
count_all = main(user, password, parser_string, replace_string, replace_tag)
finish_time = dt.now()
print('Всего репозиториев с хуками: {}'.format(str(count_all[0])))
print('Время окончания: {}'.format(str(dt.now())))
delta_time = finish_time - start_time
print('Всего затрачено: {}'.format(str(delta_time)))
print('В среднем на один хук: {}'. format(str(delta_time/count_all[0])))