import sys
import argparse
import datetime
import dateutil.parser
import json
import chinese_calendar

parser = argparse.ArgumentParser()
parser.add_argument('filename', metavar='FILE', nargs='?')
parser.add_argument('start', default='09:00', nargs='?')
parser.add_argument('end', default='18:00', nargs='?')
args = parser.parse_args()

start_hh, start_mm = args.start.split(":")
end_hh, end_mm = args.end.split(":")

fp = None
if not args.filename:
    fp = sys.stdin
else:
    fp = args.filename

class OverTime(json.JSONEncoder):
    def __init__(self, date, name):
        self.day = date.strftime("%Y-%m-%d")
        self.start = None
        self.end = None
        self.name = name
        self.holiday = False
        self.holiday_name = ''
        self.workday = False
        self.lieu = False

    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.strftime("%Y-%m-%d %H:%M:%S")
        return super(ExtendJSONEncoder, self).default(obj)

    def __repr__(self):
        return json.dumps(self.__dict__, default=self.default)

def work_start_time(date):
    return date.replace(hour=int(start_hh), minute=int(start_mm))

def work_end_time(date):
    return date.replace(hour=int(end_hh), minute=int(end_mm))

def midnight(date):
    return date.replace(hour=0, minute=0)

def overtime(worktimes):
    data = {}
    for name in worktimes:
        for worktime in worktimes[name]:
            start = dateutil.parser.parse(worktime['start']) if worktime['start'] else None
            end = dateutil.parser.parse(worktime['end']) if worktime['end'] else None
            today = dateutil.parser.parse(worktime['day'])
            yesterday = today - datetime.timedelta(1)
            tommorrow = today + datetime.timedelta(1)

            if name not in data:
                data[name] = []
            w = data[name]

            overtime = None
            if start is not None and start < work_start_time(today):
                overtime = OverTime(yesterday, name)
                overtime.start = work_end_time(yesterday)
                overtime.end = start

            if end is not None and end > work_end_time(today) and end < tommorrow:
                overtime = OverTime(today, name)
                overtime.start = work_start_time(today)
                overtime.end = end

        w.append(overtime)

    return data


data = overtime(json.load(fp))
for name in data:
    for o in data[name]:
        if o is not None:
            o.workday = chinese_calendar.is_workday(o.start)
            o.lieu = chinese_calendar.is_in_lieu(o.start) 
            if not o.workday:
                o.holiday, o.holiday_name = chinese_calendar.get_holiday_detail(o.start)
                if not o.holiday_name:
                    o.holiday_name = o.start.weekday()+1


def serialize(obj):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, datetime.datetime):
        return obj.strftime("%Y-%m-%d %H:%M:%S")

    return obj.__dict__

print(json.dumps(data, default=serialize))
