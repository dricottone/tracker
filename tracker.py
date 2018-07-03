#!/usr/bin/python3
import datetime

def getrecorddate(datetimeobj=None):
    """
    Converts a datetime object into a record date string.
    """
    if datetimeobj is None:
        datetimeobj = datetime.datetime.today()
    return datetimeobj.strftime(r'%y-%m-%d') #YY-MM-DD

def fromrecorddate(recorddate):
    """
    Converts a record date string into a datetime object.
    """
    return datetime.datetime.strptime(recorddate, r'%y-%m-%d')

class Project:
    def __init__(self):
        self.time = 0
        self.records = dict()
        self.url = ''
        self.path = ''
        self.archive = ''
        self.datamap = 1
        self.notes = ''

    def add(self, hours, date=None):
        """
        Adds a record with hours under date.
        """
        if date is None:
            date = getrecorddate()
        self.records[date] += hours
        self.time += hours

    def remove(self, hours, date=None):
        """
        Subtracts hours from a record.
        """
        neghours = 0 - hours
        self.add(neghours, date)

    def since(self, date):
        """
        Returns total time since date.
        """
        time = 0
        for record in self.records:
             if fromrecorddate(record) > date:
                 time += self.record[record]
        return time

class ProjectList:
    def __init__(self):
        self.sheet = dict()

    def create(self, name):
        """
        Add a project under name to the sheet.
        """
        self.sheet[name] = Project()

    def delete(self, name):
        """
        Delete a project from the sheet.
        """
        self.sheet.pop(name)

    def since(self, date):
        """
        Returns tuple of total time since date and every project with time
        since date.
        """
        time, projects = 0, list()
        for project in self.sheet:
             result = self.sheet[project].since(date)
             if result > 0:
                 time += result
                 projects.append(project)
        return (time, projects)

    def readjson(self, filename):
        """
        Imports projects and records from a JSON file.
        """
        with open(filename, 'r') as f:
            j = json.load(f)
        for project in j:
            self.create(project)
            for date in j[project]:
                self.sheet[project].add(hours, date)

    def writejson(self, filename):
        """
        Exports projects and records to a JSON file.
        """
        j = dict()
        for project in self.sheet:
            j[project] = dict()
            for date in self.sheet[project]:
                j[project][record] = self.sheet[project].records[date]
        with open(filename, 'w') as f:
            json.write(f, j)

if __name__ == '__main__':
    P = ProjectList().fromjson(r'C:\Users\DominicRicottone\Documents\ProjectList.json')
    lastweek = datetime.datetime.today() - datetime.timedelta(days=7)
    print('This past week you have worked ', str(P.since(lastweek)[0]), ' hours!')

