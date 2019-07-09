import sys
import argparse
import datetime
import dateutil.parser
import re
import json

parser = argparse.ArgumentParser()
parser.add_argument('filename', metavar='FILE', nargs='?')
args = parser.parse_args()

class Author():
    split_author = re.compile(r'Author: (.*) <(.*)>')
    def __init__(self, name, mail):
        self.name = name
        self.mail = mail

    @staticmethod
    def parse(s):
        m = Author.split_author.match(s)
        if m is not None:
            return Author(m[1], m[2])
        raise Exception("invalid author", s)

    def __repr__(self):
        return json.dumps(self.__dict__)

class Commit(json.JSONEncoder):
    def __init__(self, commit_id):
        self.commit_id = commit_id
        self.author = None
        self.date = None #dateutil.parser.parse(date)
        self.msg = ''#msg
    
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.strftime("%Y-%m-%d %H:%M:%S")
        elif isinstance(obj, Author):
            return obj.__dict__
        return super(ExtendJSONEncoder, self).default(obj)

    def __repr__(self):
        return json.dumps(self.__dict__, default=self.default)

def git_log(f):
    commits = []
    commit = None
    for line in f.readlines():
        if line.startswith("commit"):
            _, commit_id = line.split()
            commit = Commit(commit_id)
            commits.append(commit)
        elif line.startswith("Author:"):
            commit.author = Author.parse(line)
        elif line.startswith("Date:"):
            _, date = line.split(" ", 1)
            commit.date = dateutil.parser.parse(date)
        else:
            l = line.lstrip()
            if l:
                commit.msg += l

    return commits

fp = None
if not args.filename:
    fp = sys.stdin
else:
    fp = args.filename


print(git_log(fp))
