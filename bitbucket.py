#coding=utf-8
import json
import httplib2
import urllib
import base64
import subprocess
import copy
import re
import uuid
from array import array
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning

# try:
#     from .config import AS
#     SERVER_URLS = AS['bitbucket']['urls']
#     USER, PASSWORD = AS['bitbucket']['user'], AS['bitbucket']['password']
# except:
#     print("Run in local mode")

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

restrictions = [{
    "main_type": "fast-forward-only", "matcherId": "refs/heads/master",
    "displayId": "master", "typeId": "BRANCH", "typeName": "Branch",
    "users": [], "groups": [], "accessKeys": []
}, {
    "main_type":"no-deletes", "matcherId":"refs/heads/master",
    "displayId": "master", "typeId": "BRANCH", "typeName": "Branch",
    "users": [], "groups": [], "accessKeys": []
}, {
    "main_type": "pull-request-only", "matcherId": "refs/heads/master",
    "displayId": "master", "typeId": "BRANCH", "typeName": "Branch",
    "users":[], "groups":[], "accessKeys":[]
}, {
    "main_type":"read-only", "matcherId": "refs/heads/master",
    "displayId": "master", "typeId": "BRANCH", "typeName": "Branch",
    "users":[], "groups":["{group}"], "accessKeys":[]
}, {
    "main_type": "fast-forward-only", "matcherId": "RELEASE",
    "displayId": "Release", "typeId": "MODEL_CATEGORY", "typeName": "Branching model category",
    "users": [], "groups": [], "accessKeys": []
}, {
    "main_type": "no-deletes", "matcherId": "RELEASE",
    "displayId": "Release", "typeId": "MODEL_CATEGORY", "typeName": "Branching model category",
    "users": [], "groups": ["{group}"], "accessKeys": []
}, {
    "main_type": "read-only", "matcherId": "refs/tags/*",
    "displayId": "refs/tags/*", "typeId": "PATTERN", "typeName": "Pattern",
    "users": [], "groups": ["{group}"], "accessKeys": []
}]

class BitBucket:
    urls = {
        'main': {
            'url': '/'
        },
        'login': {
            'url': '/j_atl_security_check',
            'params' : {
                'j_username': '{login}',
                'j_password': '{password}',
                'submit': 'Log in'
            },
            'headers': {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Upgrade-Insecure-Requests': '1'
            },
            'in_body': True
        },
        'projects': {
            'url': '/rest/api/1.0/projects',
            'params': {
                "key": '{project_name}',
                "name": '{name}',
                "description": '{name}'
            },
            'json': True
        },
        'repos': {
            'url': '/rest/api/1.0/projects/{project_name}/repos',
            'params': {
                "name": '{repos_name}',
                "scmId": "git",
                "forkable": True
            },
            'json': True
        },
        'project_restrictions':{
            'url': '/rest/branch-permissions/2.0/projects/{project_name}/restrictions',
            'params':{
                'type':'{types}',
                'matcher':{
                    'id':'{id}',
                    'displayId':'{displayId}',
                    'type':'{type}',
                    'active':'{active}'
                },
                'users':'{users}',
                'groups': '{groups}',
                'accessKeys': '{accessKeys}'
            },
            'json': True
        },
        'restrictions': {
            'url': '/rest/branch-permissions/latest/projects/{project_name}/repos/{repos_name}/restrictions',
            'params':{
                'type':'{types}',
                'matcher':{
                    'id':'{id}',
                    'displayId':'{displayId}',
                    'type':'{type}',
                    'active':'{active}'
                },
                'users':'{users}',
                'groups': '{groups}',
                'accessKeys': '{accessKeys}'
            },
            'json': True
        },
        'permissions_users': {
            'url': '/rest/api/1.0/projects/{project_name}/repos/{repos_name}/permissions/users',
            'params': {
                'name': '{name}',
                'permission': '{permission}'
            },
            'json': False
        },
        'permissions_users_del': {
            'url': '/rest/api/1.0/projects/{project_name}/repos/{repos_name}/permissions/users',
            'params': {
                'name': '{name}',
            },
            'json': False
        },
        'permissions_users_in_project': {
            'url': '/rest/api/1.0/projects/{project_name}/permissions/users',
            'params': {
                'name': '{name}',
                'permission': '{permission}'
            },
            'json': False
        },
        'permissions_users_in_proj': {
            'url': '/rest/api/1.0/projects/{project_name}/permissions/users',
            'params': {
                'name': '{name}'
            },
            'json': False
        },
        'permissions': {
            'url': '/rest/api/1.0/projects/{project_name}/repos/{repos_name}/permissions/groups',
            'params': {
                'name': '{name}',
                'permission': '{permission}'
            },
            'json': False
        },
        'groups': {
            'url': '/rest/api/1.0/admin/groups',
            'params': {
                'name': '{name}'
            },
            'json': False
        },
        'users': {
            'url': '/admin/users',
            'params': {
                'start': '0',
                'limit': '50',
                'avatarSize': '48',
                'filter': '{username}'
            },
            'headers': {'Content-Type': 'application/json',
                        'Accept': 'application/json, text/javascript, */*; q=0.01'}
        },
        'remove_user': {
            'url': '/rest/api/1.0/admin/users',
            'params': {
                'name': '{username}'
            }
        },
        'user': {
            'url': '/rest/api/1.0/admin/users',
            'params': {
                'name': '{username}',
                'fullname': 'ttt',
                'emailAddress': 'ttt@ttt.ru',
                'password': str(uuid.uuid4())[:10],
                'displayName': 'ttt',
                'addToDefaultGroup': False
            }
        },
         'repos_delete': {
            'url': '/rest/api/1.0/projects/{project_name}/repos/{repos_name}',
            'json': False
        },
         'project_delete': {
            'url': '/rest/api/1.0/projects/{project_name}',
            'json': False
        },
        'get_group_users': {
            'url': '/rest/api/1.0/admin/groups/more-members',
            'params': {
                'context': '{group_name}'
            }
        },
        'get_user_groups': {
            'url': '/rest/api/1.0/admin/users/more-members',
            'params': {
                'context': '{user_name}'
            }
        },
        'get_user_info':{
            'url':'/rest/api/latest/users/{user_name}',
            'json':True
        },
        'repos_move': {
            'url': '/rest/api/1.0/projects/{project_name}/repos/{repos_name}',
            'params': {
                "name": "{new_repos_name}",
                "forkable": True,
                "project": {
                    "key": "{new_ci}"
                },
                "public": False
            },
            'json': True
        },
        'user2group': {
            'url': '/admin/groups/add-users',
            'params': {
                "group": "{group}",
                "users": ["{username}"]
            },
            'headers': {'Accept': 'application/json, text/javascript, */*; q=0.01'},
            'json': True
        },
        'search': {
            'url': '/rest/search/latest/search',
            'params': {
                "query": "{project_name}",
                "entities": {"repositories":{}},
                "limits": {"primary":9}
            },
            'json': True
        },
        'repo_ssh_key': {
            'url': '/rest/keys/1.0/projects/{project_name}/repos/{repos_name}/ssh',
            'params': {
                'key': {
                    'text': '{ssh_key}'
                },
                'permission': ''
            },
            'json': True
        },
        'project_ssh_key': {
            'url': '/rest/keys/1.0/projects/{project_name}/ssh',
            'params': {
                'key': {
                    'text': '{ssh_key}'
                },
                'permission': ''
            },
            'json': True
        },
        'get default reviewers': {
            'url': '/rest/default-reviewers/1.0/projects/{project_name}/repos/{repos_name}/conditions'
        },
        'add default reviewers': {
            'url': '/rest/default-reviewers/1.0/projects/{project_name}/repos/{repos_name}/condition',
            'params': {
                'sourceMatcher': {}, #{id: "any", type: {id: "ANY_REF"}},
                'targetMatcher': {}, #{id: "refs/heads/master", type: {id: "BRANCH"}},
                "reviewers": [],
                "requiredApprovals":1
            },
            "json": True
        },
        'update default reviewers': {
            'url': '/rest/default-reviewers/1.0/projects/{project_name}/repos/{repos_name}/condition/{rowid}',
            'params': {
                'sourceMatcher': {}, #{id: "any", type: {id: "ANY_REF"}},
                'targetMatcher': {}, #{id: "refs/heads/master", type: {id: "BRANCH"}},
                "reviewers":[],
                "requiredApprovals":1
            },
            "json": True
        },
        'get_project_hooks': {
            'url': '/rest/api/latest/projects/{project_name}/repos/{repos_name}/settings/hooks/com.ngs.stash.externalhooks.external-hooks%3Aexternal-post-receive-hook/settings'
        },
        'set_project_hooks':{
            'url':'/rest/api/latest/projects/{project_name}/repos/{repos_name}/settings/hooks/com.ngs.stash.externalhooks.external-hooks%3Aexternal-post-receive-hook/enabled',
            'params':{
                'params':'''--sync\r\n--sigma-remote=ssh://git@bitbucket.org/devops/repos.git\r\n--mail-list="example@youdomain.ru"\r\n--jenkins-job-url=https://jenkins.org/job/somefolder/job/somejob/''',
                'exe':'post-commit-common.sh',
                'safe_path': True
            },
            "json": True
        }
    }

    def __request(self, url, method="GET", headers=None, verify=False, body=None):
        if headers is not None and isinstance(headers, dict):
            # print(self.session.headers)
            # print(method, url)
            self.session.headers.update(headers)
        if method == "GET":
            resp = self.session.request(url=url, method=method, verify=verify)
        #elif method == "POST":
        else:
            resp = self.session.request(url=url, method=method, data=body, verify=verify)

        if (int(resp.status_code) < 200 or int(resp.status_code) > 299) and int(resp.status_code) != 409:
            raise Exception('\n'.join(["Error status code: " + str(resp.status_code), 
                                       "request: " + method + " " + url, "headers: " + str(self.session.headers), 
                                       "data: " + str(body), "response: " + str(resp)]))

        content = resp.text
        response = {'headers': resp.headers, 'status_code': resp.status_code, "status": str(resp.status_code)}
        return response, content

    def __init__(self, server_url, user, password, gitPath='~/Documents/bitbucket/tmp', is_windows=False):
        self.gitPath = gitPath
        self.is_windows = is_windows

        self.server_url = server_url
        if self.server_url[-1] == '/':
            self.server_url = self.server_url[:-1]

        self.userAndPass = user+":"+password
        hashed_data = base64.b64encode(self.userAndPass.encode()).decode("ascii")
        self.headers = {'Content-Type': 'application/json', "Authorization": "Basic %s" % hashed_data}

        method = 'GET'
        url = '/rest/api/1.0/projects'

        self.session = requests.Session()
        response, content = self.__request(self.server_url+url, method=method, headers=self.headers)

        if str(response['status_code']) != '200':
            raise Exception('Status code ['+str(response['status_code'])+'] is not equal 200')

    def get_server_url(self):
        return self.server_url
    
    def delete_project(self, project_name):
        params = {'project_name': project_name}
        return self.execute('DELETE', 'project_delete', params)
    
    def delete_repo(self, project_name, repos_name):
        params = {'project_name': project_name, 'repos_name': repos_name}
        return self.execute('DELETE', 'repos_delete', params)
    
    def move_repo(self, project_name, repos_name, new_ci, new_repos_name):
        params = {'project_name': project_name, 'repos_name': repos_name, 'new_ci': new_ci, 'new_repos_name': new_repos_name}
        return self.execute('PUT', 'repos_move', params)

    def format(self, data, params, recursive=True):
        data = copy.deepcopy(data)
        if isinstance(data, dict):
            for key in data.keys():
                if key in params.keys():
                    data[key] = params[key]
                data[key] = self.format(data[key], params)
        if isinstance(data, str):
            return data.format(**params)
        if isinstance(data, list):
            data = [self.format(node, params) for node in data]
        return data

    def execute(self, method, group, params=None, limit=10000, start=0, use_get_params=False):
        # http = httplib2.Http(disable_ssl_certificate_validation=True)

        # headers = None
        headers = copy.deepcopy(self.headers)
        if 'headers' in self.urls[group]:
            headers.update(self.urls[group]['headers'])

        url = copy.deepcopy(self.urls[group]['url'])
        params_dict = {}
        if 'params' in self.urls[group]:
            params_dict = copy.deepcopy(self.urls[group]['params'])
        in_body = False

        if ('in_body' in self.urls[group]):
            in_body = self.urls[group]['in_body']

        if not (params is None):
            url = url.format(**params)


#         print(headers)
        if method == 'GET':
            if params_dict != {} and use_get_params:
#                 print(params_dict)
                url_params = urllib.parse.urlencode(self.format(params_dict, params))
                url = url + '?' +url_params
#             print(self.server_url+url)
            # response, content = http.request(self.server_url+url, method=method, headers=headers)
            response, content = self.__request(self.server_url+url, method=method, headers=headers)
#             print([response, content])
            res = {}
            try:
                tmp_res = json.loads(content)
                res = tmp_res
                while (isinstance(tmp_res, dict)) and ('isLastPage' in tmp_res.keys()) and (not tmp_res['isLastPage']):
                    start = str(tmp_res['nextPageStart'])
                    limit = str(limit)
                    if '?' in self.server_url+url:
                        exec_url = self.server_url+url+'&start='+start+'&limit='+limit
                    else:
                        exec_url = self.server_url+url+'?start='+start+'&limit='+limit
                    # response, content = http.request(exec_url,  
                    #                                  method=method, headers=headers)
                    response, content = self.__request(exec_url, method=method, headers=headers)
                    tmp_res = json.loads(content)
                    res['values'].extend(tmp_res['values'])
                    res['size'] = res['size']+tmp_res['size']
            except Exception as e:
                return response, res
#                 return response, content
        else:
            if ('json' in self.urls[group].keys()) and self.urls[group]['json']:
#                 print(self.server_url+url)
                #print(self.format(params_dict, params))
                # response, content = http.request(self.server_url+url, method=method, headers=headers, body=json.dumps(self.format(params_dict, params)))
                response, content = self.__request(self.server_url+url, method=method, headers=headers, body=json.dumps(self.format(params_dict, params)))
            else:
#                print(params_dict, params)
                url_params = urllib.parse.urlencode(self.format(params_dict, params))
                if in_body:
#                     print(['in_body', self.server_url+url, url_params])
                    # response, content = http.request(self.server_url+url, body=url_params, method=method, headers=headers)
                    response, content = self.__request(self.server_url+url, body=url_params, method=method, headers=headers)
                else:
#                     print(['out_body', self.server_url+url, url_params])
                    # response, content = http.request(self.server_url+url+'?'+url_params, method=method, headers=headers)
                    response, content = self.__request(self.server_url+url+'?'+url_params, method=method, headers=headers)
            try:
                if response['status'] == '204' or content == b'' or content == '':
                    res = ''
                else:
                    res = json.loads(content)
                pass
            except Exception as e:
                print('Exception', [response, content])
                return response, e
#                 return response, content
        return response, res

    # Создание мастер ветки
    def create_master_branch_windows(self, project_name, repos_name, names):
        params = {'project_name': project_name, 'repos_name':repos_name}
        params.update(names)

        readme = [
        #             'Introduction'
        #             '============'
            'АС: {name}',
            'ФП: {fname}'
        ]
        bashCommand = [
            "set GIT_SSL_NO_VERIFY=1",
            "(if not exist "+ self.gitPath+" mkdir "+ self.gitPath+")",
            "cd " + self.gitPath,
            "(mkdir {repos_name} > NUL)",
            "cd {repos_name}",
            "git init",
            'echo ' +readme[0] + ' > README.md',
            'echo ' +readme[1] + ' >> README.md',
            "git add --all",
            'git commit -m "Initial Commit"',
            "git push " + self.server_url.replace('://', '://'+self.userAndPass+'@') +"/scm/{project_name}/{repos_name}.git --all",
            "cd ..",
            'rmdir {repos_name} /s /q',
            "cd .."
        ]

        cmd_line = ' && '.join(bashCommand).format(**params).encode("utf-8").decode("cp866")
#         print(cmd_line)
        process = subprocess.getoutput(cmd_line)
        # print(process.encode("cp1251").decode("cp866"))
#         print(process.encode("cp1251").decode("cp866"))
        return None, process.encode("cp1251").decode("cp866")

    def create_master_branch_nix(self, project_name, repos_name, names):
        params = {'project_name': project_name, 'repos_name':repos_name}
        params.update(names)

        readme = [
#             'Introduction'
#             '============'
            'АС: {name}',
            'ФП: {fname}'
        ]
        bashCommand = [
            "cd " + self.gitPath,
            "git clone http://someone:123456@localhost:7990/scm/{project_name}/{repos_name}.git",
            "cd {repos_name}",
            "git init",
            "echo '" + "\r\n".join(readme) + "' > README.md",
            "git add --all",
            'git commit -m "Initial Commit"',
            "git push " + self.server_url.replace('://','://'+self.userAndPass+'@') +"/scm/{project_name}/{repos_name}.git --all",
            "cd ..",
            "rm -rf {repos_name}"
        ]
        process = subprocess.getoutput(' && '.join(bashCommand).format(**params))
        return None, process

    def create_master_branch(self, project_name, repos_name, names):
        if self.is_windows:
            return self.create_master_branch_windows(project_name, repos_name, names)
        return self.create_master_branch_nix(project_name, repos_name, names)

    # Работа с проектами
    def create_project(self, project_name, name, description):
        return self.execute('POST', 'projects', {'project_name': project_name, 'name': name, 'description':description})
    
    def auth(self):
        return self.execute('GET', 'main')
    
    def get_projects(self):
        return self.execute('GET', 'projects')

    def get_hooks(self, project_name, repos_name):
        return self.execute('GET', 'get_project_hooks', {'project_name': project_name, 'repos_name': repos_name})

    def set_hooks(self, project_name, repos_name, data):
        return self.execute('PUT', 'set_project_hooks', {'project_name': project_name, 'repos_name': repos_name, 'params':data}) 

    def get_project_ids(self):
        response, result = self.get_projects()
        self.existed_projects = [node['key'] for node in result['values']]
#         self.existed_projects.extend([node['name'].split()[0] for node in result['values']])
        self.existed_projects = list(set(self.existed_projects))
        return self.existed_projects

    # Работа с репозиториями
    def create_repos(self, project_name, repos_name):
        return self.execute('POST', 'repos', {'project_name': project_name, 'repos_name': repos_name})

    def get_repos(self, project_name):
        return self.execute('GET', 'repos', {'project_name': project_name})

    def get_repo_ids(self, project_name):
        self.get_project_ids()
        response, result = self.get_repos(project_name)
        self.existed_repos = [node['name'] for node in result['values']]
        self.existed_repos = list(set(self.existed_repos))
        self.existed_repos.sort()
        return self.existed_repos

    # Работа с группами
    def create_group(self, name):
        return self.execute('POST', 'groups', {'name': name})

    def get_groups(self):
        return self.execute('GET', 'groups')

    def get_group_names(self):
        response, result = self.get_groups()
        existed_groups = [node['name'] for node in result['values']]
        existed_groups = list(set(existed_groups))
        existed_groups.sort()
        return existed_groups

    # Работа с ограничениями
    def create_restriction(self, project_name, repos_name, restriction):
        params = {'project_name': project_name, 'repos_name':repos_name}
        params.update(restriction)
        return self.execute('POST', 'restrictions', params)


    def get_restrictions(self, project_name, repos_name):
        return self.execute('GET', 'restrictions', {'project_name': project_name, 'repos_name':repos_name})

    def get_project_restrictions(self, project_name):
        return self.execute('GET', 'project_restrictions', {'project_name': project_name})

    def set_project_restrictions(self, project_name, restrict):
        params = {'project_name': project_name}
        params.update(restrict)
        return self.execute('POST', 'project_restrictions', params)
    
    def set_restrictions(self, project_name, repos_name, restrict):
        params = {'project_name': project_name, 'repos_name': repos_name}
        params.update(restrict)
        return self.execute('POST', 'restrictions', params)

    def create_permission_user(self, project_name, repos_name, permission):
        params = {'project_name': project_name, 'repos_name':repos_name}
        params.update(permission)
        return self.execute('PUT', 'permissions_users', params)

    def delete_permission_user(self, project_name, repos_name, name):
        params = {'project_name': project_name, 'repos_name':repos_name}
        params.update(permission)
        return self.execute('DELETE', 'permissions_users_del', params)

    # Работа с разрешениями
    def create_permission(self, project_name, repos_name, permission):
        params = {'project_name': project_name, 'repos_name':repos_name}
        params.update(permission)
        return self.execute('PUT', 'permissions', params)

    def create_permission_user_in_project(self, project_name, permission, user):
        params = {'project_name': project_name, 'name':user, 'permission':permission}
        return self.execute('PUT', 'permissions_users_in_project', params)

    def delete_permission_user_in_project(self, project_name, user):
        params = {'project_name': project_name, 'name':user}
        return self.execute('DELETE', 'permissions_users_in_proj', params)

    def get_permissions(self, project_name, repos_name):
        return self.execute('GET', 'permissions', {'project_name': project_name, 'repos_name':repos_name})

    def get_permissions_users_in_project(self, project_name):
        return self.execute('GET', 'permissions_users_in_project', {'project_name': project_name})

    def create_user(self, username):
        data = {'username': username}
        return self.execute('POST', 'user', data)

    def delete_group(self, name):
        data = {'name': name}
        return self.execute('DELETE', 'groups', data)
    
    def delete_user(self, username):
        data = {'username': username}
        return self.execute('DELETE', 'remove_user', data)

    def get_users(self):
        data = {}
        return self.execute('GET', 'users', data)

    def get_group_users(self, group_name):
        data = {'group_name': group_name}
        return self.execute('GET', 'get_group_users', data, use_get_params=True)

    def get_user_groups(self, user_name):
        data = {'user_name': user_name}
        return self.execute('GET', 'get_user_groups', data, use_get_params=True)

    def get_user(self, username):
        data = {'username': username}
        return self.execute('GET', 'users', data, use_get_params=True)

    def get_user_info(self, user_name):
        data = {'user_name': user_name}
        return self.execute('GET', 'get_user_info', data)

    def add_user2group(self, username, group):
        data = {'username': username, 'group': group}
        return self.execute('POST', 'user2group', data)

    def search(self, project_name):
        data = {'project_name': project_name}
        return self.execute('POST', 'search', data)

    def set_repo_ssh_key(self, project_name, repos_name, ssh_key, permission):
        #print('!!!!:' ,ssh_key,permission)
        data = {'project_name': project_name, 'repos_name': repos_name, 'ssh_key': ssh_key, 'permission':permission}
        return self.execute('POST', 'repo_ssh_key', data)

    def get_repo_ssh_key(self, project_name, repos_name):
        data = {'project_name': project_name, 'repos_name': repos_name}
        return self.execute('GET', 'repo_ssh_key', data)

    def get_project_ssh_key(self, project_name):
        data = {'project_name': project_name}
        return self.execute('GET', 'project_ssh_key', data)

    def set_merge_checks(self, project_name, repos_name, users, pattern=None):
        data = {'project_name': project_name, 'repos_name': repos_name, 'users': users}
        if pattern is not None:
            data.update({"pattern": pattern})
        return self.execute('PUT', 'merge_checks', data)

    def get_default_reviewers(self, project_name, repos_name):
        data = {'project_name': project_name, 'repos_name': repos_name}
        return self.execute('GET', 'get default reviewers', data)

    def add_default_reviewers(self, project_name, repos_name, params):
        data = dict(params)
        data.update({'project_name': project_name, 'repos_name': repos_name})
        return self.execute('POST', 'add default reviewers', data)

    def update_default_reviewers(self, project_name, repos_name, rowid, params):
        data = dict(params)
        data.update({'project_name': project_name, 'repos_name': repos_name, 'rowid': rowid})
        return self.execute('PUT', 'update default reviewers', data)

# bb_server = None

# try:
#     # _http = httplib2.Http(disable_ssl_certificate_validation=True)
#     for _url in SERVER_URLS:
#         try:
#             print('Try:', _url)
#             # res = _http.request(_url)
#             bb_server = BitBucket(_url, USER, PASSWORD, gitPath='tmp', is_windows=True)
#             print('Used:', _url)
#             break
#         except Exception as exc:
#             print(exc)
# except:
#     pass
    