import shutil
import os
from git import Repo, Git, config, GitCommandError

my_account = os.environ.get('GITHUB_USERNAME', None)

def push_to_github(local_dir, repo_path, commit_message='No commit message was set.'):
    repo_list = repo_path.split('/')
    try:
        n = repo_list.index('tree')
    except ValueError:
        n = len(repo_list)
    repo_name = os.path.join(*repo_list[:n])
    account = my_account
    repo_url = '/'.join(['https://' + os.environ.get('GITHUB_USERNAME', None) + ':' + os.environ.get('GITHUB_PASSWORD', None) + '@github.com',account,repo_name])
    branch = repo_list[-1] if 'tree' in repo_list else None

    print(repo_url)

    os.system('cd')
    git_dir = os.path.join('dest_repo', repo_name)
    try:
        shutil.rmtree(git_dir)
        shutil.rmtree('dest_repo')
    except:
        pass
    os.system('md dest_repo')
    kwargs = { 'url': repo_url, 'to_path': git_dir }
    if branch:
        kwargs['branch'] = branch
    repo = Repo.clone_from(**kwargs)
    os.chdir(git_dir)
    os.system(' '.join(['cp', '-rf', os.path.join('..', '..', local_dir, '.'), '.']))

    origin = repo.remotes[0]

    gitcmd = Git('.')
    gitcmd.config('--add', 'user.name', os.environ.get('GITHUB_USERNAME', None))
    gitcmd.config('--add', 'user.email', os.environ.get('GITHUB_EMAIL', None))
    repo.git.add(A=True)
    repo.git.add(u=True)
    repo.index.commit(commit_message)
    repo.git.push('--set-upstream', 'origin', branch)
    stats = repo.head.commit.stats.total

    os.chdir('../..')
    shutil.rmtree('dest_repo')
    return stats

def clone_from_github(repo_name,account=my_account):
    local_dir = repo_name
    repo_url = '/'.join(['https://' + os.environ.get('GITHUB_USERNAME', None) + ':' + os.environ.get('GITHUB_PASSWORD', None) + '@github.com',account,repo_name])
    if os.path.exists(local_dir):
        shutil.rmtree(local_dir)
    try:
        repo = Repo.clone_from(repo_url,local_dir)
    except GitCommandError as e:
        None

def copy_from_github(repo_name,account=my_account):
    repo_url = '/'.join(['https://' + os.environ.get('GITHUB_USERNAME', None) + ':' + os.environ.get('GITHUB_PASSWORD' + '@github.com',account,repo_name])
    repo = Repo.clone_from(repo_url,'_temp')
    shutil.rmtree('_temp/.git')
    os.system('cp -r {} {}'.format('_temp/.', repo_name))
    shutil.rmtree('_temp')
    return { 'file_count': len(os.listdir(repo_name)) }

if __name__ == '__main__':
    push_to_github('test_repo', remote_dir='https://github.com/' + os.environ.get('GITHUB_USERNAME', None) + '/test_repo')