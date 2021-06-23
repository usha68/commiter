import itertools
from collections import defaultdict

import gitlab
from django.shortcuts import render
from .forms import UserForm

GITLAB_URL = 'https://gitwork.ru/'
ACCESS_TOKEN = '9asxVxQbcNqVxQ-CBVfc'
import urllib3
from django.shortcuts import render
from django.http import HttpResponse
from .forms import UserForm


def index(request):
    return render(request, 'main/index.html')


def visual(request):
    if request.method == "POST":
        id = request.POST.get("id")
        return HttpResponse("<h2>Hello, {0}</h2>".format(id))
    else:
        userform = UserForm()
        return render(request, "main/visual.html", {"form": userform})


def listz(request):
    gl = gitlab.Gitlab(GITLAB_URL, ACCESS_TOKEN)
    gl.auth()
    num_project = []
    id_project = gl.projects.list(all=True, visibility='private')
    for item in id_project:
        num_project.append(item.__dict__['_attrs']['name_with_namespace'])
    dict_project = dict(enumerate(num_project))
    return render(request, 'main/list.html', {'dict_project': dict_project.values()})


def info_project(request):
    gl = gitlab.Gitlab(GITLAB_URL, ACCESS_TOKEN)
    gl.auth()
    id_project = []
    name_with_namespace = []
    path_project = []
    name_list = []
    id_list = gl.projects.list(all=True, visibility='private')
    for item in id_list:
        name_with_namespace.append(item.__dict__['_attrs']['name_with_namespace'])
    for it in id_list:
        path_project.append(it.__dict__['_attrs']['path_with_namespace'])
    for ite in id_list:
        id_project.append(ite.__dict__['_attrs']['id'])
    for its in id_list:
        name_list.append(its.__dict__['_attrs']['name'])
    dict_id = dict(enumerate(id_project))
    dict_name_namespace = dict(enumerate(name_with_namespace))
    dict_path = dict(enumerate(path_project))
    dict_name = dict(enumerate(name_list))
    return render(request, 'main/info.html',
                  {'data': zip(dict_id.values(), dict_name_namespace.values(), dict_path.values(), dict_name.values())},)



def get_stats_per_diff_file(diff_file, commit):
    added, deleted = 0, 0
    for line in diff_file['diff'].split('\n'):
        added += int(line.startswith('+'))
        deleted += int(line.startswith('-'))
    return {
        'added': added,
        'deleted': deleted,
        'path': diff_file['new_path'],
        'commit': commit
    }


def get_stats_per_commit(project, short_id):
    commit = project.commits.get(short_id)
    print(commit)
    diff = commit.diff(page=1, per_page=100)
    for i in diff:
        yield get_stats_per_diff_file(i, commit)


def get_stats_per_project(project_id=1992):
    gl = gitlab.Gitlab(GITLAB_URL, ACCESS_TOKEN)
    gl.auth()
    project = gl.projects.get(project_id)
    commits = project.commits.list()
    short_id_list = list(item.__dict__['_attrs']['short_id'] for item in commits)
    return list(itertools.chain.from_iterable(get_stats_per_commit(project, x) for x in short_id_list))

def get_commits(request, project_id):
    changes = get_stats_per_project(project_id)
    files = set(x['path'] for x in changes)


    files_with_changes = list( {
                                   'filename': file,
                                   'changes': list(x for x in changes if x['path'] == file)
                               } for file in files
                               )

    changes_by_commit = defaultdict(list)
    for change in changes:
        changes_by_commit[change['commit'].short_id].append(change)

    def get_changes_for_file(changelist, file):
        for change in changelist:
            if change['path'] == file:
                return change
        return {'added': '', 'deleted': ''}

    overall_header = [' ', *changes_by_commit.keys()]
    overall_changes = list( {
                                'filename': file,
                                'changes': list(get_changes_for_file(x, file) for x in changes_by_commit.values())
                            } for file in files)


    return render(request, 'main/get_commits.html', {
        'files_with_changes': files_with_changes,
        'overall_header': overall_header,
        'overall_changes': overall_changes
    })

