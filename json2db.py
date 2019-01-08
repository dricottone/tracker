#!/usr/bin/env python3.7
import json, os, datetime, decimal
import dirutils, sqlutils

old = os.path.join(dirutils.findbasedir(), 'tracker', 'sheet.json')
new = os.path.join(dirutils.findbasedir(), 'tracker', 'time_tracking.db')

with open(old, 'r') as f:
    j = json.load(f)

with sqlutils.open_db(new) as db:
    tbl = db.get('Time_Tracking')
    for project,records in j.items():
        for date, hours in records.items():
            _hours = decimal.Decimal(hours)
            _date = datetime.datetime.strptime(date, r'%y-%m-%d').date()
            tbl._execute(f"insert into Time_Tracking (day, project, hours) values ('{str(_date)}', '{project}', '{str(_hours)}')")

