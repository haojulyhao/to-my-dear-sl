import sys
import argparse
import datetime
import dateutil.parser
import json
import chinese_calendar
import math

parser = argparse.ArgumentParser()
parser.add_argument('filename', metavar='FILE', nargs='?')
parser.add_argument('--start', default='09:00', nargs='?')
parser.add_argument('--end', default='18:00', nargs='?')
args = parser.parse_args()

start_hh, start_mm = args.start.split(":")
end_hh, end_mm = args.end.split(":")

WEEKDAY = ["星期一","星期二","星期三", "星期四", "星期五", "星期六", "星期天"]

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
        self.duration = 0

    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.strftime("%Y-%m-%d %H:%M:%S")
        return super(ExtendJSONEncoder, self).default(obj)

    #  def __repr__(self):
    #      return json.dumps(self.__dict__, default=self.default)

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
            #  print(start, end ,today,yesterday,tommorrow,work_start_time(today),work_end_time(today))
            workday = chinese_calendar.is_workday(start)
            lieu = chinese_calendar.is_in_lieu(start) 
            holiday, holiday_name = chinese_calendar.get_holiday_detail(start)
            holiday_name = WEEKDAY[start.weekday()] if not holiday_name else holiday_name
            #  if not workday:
            #      holiday, holiday_name = chinese_calendar.get_holiday_detail(o.start)
            #      if holiday_name:
            #          o.holiday_name = holiday_name

            if name not in data:
                data[name] = {'overtime': []}
            w = data[name]['overtime']

            overtime = None
            if workday:
                # 如果首次提交时间小于上班时间，则认为是昨天的通宵加班
                if start is not None and start < work_start_time(today):
                    overtime = OverTime(yesterday, name)
                    overtime.start = work_end_time(today)
                    overtime.end = start

                # 如果最后一次提交大于下班时间，且没有到0点
                if end is not None and end > work_end_time(today) and end < tommorrow:
                    overtime = OverTime(today, name)
                    overtime.start = work_end_time(today)
                    overtime.end = end
            else:
                if start is not None and start > work_start_time(today): 
                    overtime = OverTime(today, name)
                    overtime.start = work_start_time(today)
                    if end is None:
                        overtime.end = work_end_time(today)
                    else:
                        overtime.end = end if end > work_end_time(today) else work_end_time(today)

            if overtime is  None:
                continue
            overtime.duration = math.ceil((overtime.end - overtime.start).seconds / 3600.0)
            overtime.workday = workday
            overtime.holiday = holiday
            overtime.holiday_name = holiday_name
            overtime.lieu = lieu
            w.append(overtime)

    return data


data = overtime(json.load(fp))
for name in data:
    total_hours = 0
    holiday_hours = 0 
    for o in data[name]['overtime']:
        if o is not None:
            #  o.workday = chinese_calendar.is_workday(o.start)
            #  o.lieu = chinese_calendar.is_in_lieu(o.start)
            #  o.holiday_name = o.start.weekday()+1
            if not o.workday:
                #  holiday, holiday_name = chinese_calendar.get_holiday_detail(o.start)
                #  if holiday_name:
                #      o.holiday_name = holiday_name
                holiday_hours += o.duration
            total_hours += o.duration
    data[name]['total_hours'] = total_hours
    data[name]['holiday_hours'] = holiday_hours


def serialize(obj):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, datetime.datetime):
        return obj.strftime("%Y-%m-%d %H:%M:%S")

    return obj.__dict__

print(json.dumps(data, default=serialize))
