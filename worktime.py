import argparse
import dateutil.parser
import chinese_calendar
import json
import sys
import datetime

parser = argparse.ArgumentParser()
parser.add_argument('filename', metavar='FILE', nargs='?')
parser.add_argument('start', default='09:00', nargs='*') 
parser.add_argument('end', default='17:00', nargs='*') 
args = parser.parse_args()

fp = None
if not args.filename:
    fp = sys.stdin
else:
    fp = args.filename

class WorkTime(json.JSONEncoder):
    def __init__(self, day, name):
        self.day = day
        self.start = None
        self.end = None
        self.name = name

    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.strftime("%Y-%m-%d %H:%M:%S")
        return super(ExtendJSONEncoder, self).default(obj)

    def __repr__(self):
        return json.dumps(self.__dict__, default=self.default)

def sum_worktime(commits):
    duration = {}
    commits.sort(key=lambda x:x['date'])
    for commit in commits:
        name = commit['author']['name']
        date = dateutil.parser.parse(commit['date'])
        day = date.strftime("%Y-%m-%d")
        if name not in duration:
            duration[name] = []

        w = duration[name]
        if day not in [x.day for x in w]:
            worktime = WorkTime(day, name)
            worktime.start = date
            w.append(worktime)
        else:
            worktime = w[-1]
            if (worktime.end is None) or (worktime.end < date):
                worktime.end = date

    return duration


ret = sum_worktime(json.load(fp))
print(json.dumps(ret))
