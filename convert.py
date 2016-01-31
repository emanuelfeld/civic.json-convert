import json
import requests
from collections import OrderedDict
import subprocess

from settings import ACCESS_TOKEN


def create_message(licensed=True):
    intro = """
Update civic.json file to new specification

Hi, there! Code for DC is moving to an updated civic.json
specification. This pull request formats your existing
civic.json to the new standard.

Feel free to look it over and make any updates.
    """

    outro = """

The new civic.json spec keeps the required fields from the older
one, but has a number of benefits. It:

* removes fields that are hard to maintain and get out of date quickly
* combines partner fields to be more broadly applicable
* is usable by civic tech projects outside of government, as well as inside

You'll see that DC Government is using this standard in its own repos:

https://github.com/dcgov

You can learn more about the specification requirements here:

http://open.dc.gov/civic.json

    """

    if not licensed:
        ask = """
========================
I also see that your repository has no license. 
Without a license, others have no permission to use, modify, or share your code.

This site makes it easy to add an open source license: http://choosealicense.com/
========================

        """
        outro = ask + outro
    return intro, outro


def convert(old, name, repository, description, homepage, license=''):
    with open('empty.json') as infile:
        new = json.load(infile, object_pairs_hook=OrderedDict)
    new['name'] = none_str(name).strip()
    new['description'] = none_str(description)
    new['repository'] = none_str(repository)
    new['homepage'] = none_str(homepage)
    new['license'] = none_str(license).upper()
    new['contact']['name'] = deep_hasattr(old, 'contact', 'name')
    new['contact']['email'] = deep_hasattr(old, 'contact', 'email')
    if deep_hasattr(old, 'contact', 'twitter'):
        new['contact']['url'] = 'https://twitter.com/' + old['contact']['twitter']
    new['status'] = deep_hasattr(old, 'status')
    if deep_hasattr(old, 'moreInfo'):
        new['links'].append(old['moreInfo'])
    new['thumbnail'] = deep_hasattr(old, 'thumbnailUrl')
    new['type'] = deep_hasattr(old, 'type')
    if deep_hasattr(old, 'geography'):
        new['geography'].append(old['geography'])
    if deep_hasattr(old, 'governmentPartner'):
        for partner in old['governmentPartner']:
            p = {"name": "", "email": "", "url": ""}
            p['name'] = partner
            p['url'] = old['governmentPartner'][partner]
            new['partners'].append(p)
    if deep_hasattr(old, 'communityPartner'):
        for partner in old['communityPartner']:
            p = {"name": "", "email": "", "url": ""}
            p['name'] = partner
            p['url'] = old['communityPartner'][partner]
            new['partners'].append(p)
    new['partners'].append({"name": "Code for DC", "email": "", "url": "http://codefordc.org"})
    return new


def deep_hasattr(d, *names):
    for name in names:
        if not name in d.keys():
            return ""
        d = d[name]
    if isinstance(d, str):
        d = d.strip()
    return d


def none_str(value):
    if not value:
        return ''
    else:
        return value.strip()


def subprocess_helper(cmd):
    return subprocess.check_output(cmd, universal_newlines=True)


if __name__ == '__main__':
    tracked = requests.get('https://raw.githubusercontent.com/codefordc/files/release/tracked.json').json()
    projects = tracked['projects']

    github_headers = {'Authorization': 'token {}'.format(ACCESS_TOKEN), 'Accept': 'application/vnd.github.drax-preview+json'}

    for project in [projects[0]]:
        name = project.keys()[0].strip()
        repository = project.values()[0].strip()
        repository_name = repository.split('/')[-1]
        repository_owner = repository.split('/')[-2]
        api_url = 'https://api.github.com/repos/{}/{}'.format(repository_owner, repository_name)
        print repository_owner, repository_name
        try:
            repo = requests.get(api_url, headers=github_headers).json()
            licensed = True
            try:
                license = repo['license']['key']
            except:
                licensed = False
            intro, outro = create_message(licensed)
            civic_url = 'https://raw.githubusercontent.com/{0}/{1}/civic.json'.format(repo['full_name'], repo['default_branch'])
            civic_json = requests.get(civic_url).json()
            new = convert(civic_json, name, repository, repo['description'], repo['homepage'], license)
            with open('new/' + repository_owner + '-' + repository_name + '.json', 'w') as outfile:
                json.dump(new, outfile, indent=4)
            cmd = ['sh', 'github.sh', repository, repository_owner + '-' + repository_name, intro, outro]
            print subprocess_helper(cmd)
        except:
            print "Failed", repository_owner, repository_name
