#!/usr/bin/python3
import datetime, json, decimal, pprint

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
    def __init__(self, title):
        self.title = title
        self.time = decimal.Decimal()
        self.records = dict()

        self.url = ''
        self.path = ''
        self.archive = ''
        self.datamap = 1
        self.notes = ''
    def __iter__(self):
        return ProjectIterable(self)
    def __str__(self):
        return pprint.pformat(self.records)

    def add(self, hours, date=None):
        """
        Adds a record with hours under date.
        """
        if date is None:
            date = getrecorddate()
        if 'date' in self.records:
            self.records[date] += hours
        else:
            self.records[date] = decimal.Decimal(hours)
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
                 time += self.records[record]
        return time

class ProjectIterable:
    def __init__(self, project):
        self.iterable = list(project.records.items())
        self.index = 0
    def __next__(self):
        try:
            result = self.iterable[self.index]
        except IndexError:
            raise StopIteration
        self.index += 1
        return result

class ProjectSheet:
    def __init__(self):
        self.sheet = dict()
        self.index = 0
    def __iter__(self):
        return ProjectSheetIterable(self)
    def __str__(self):
        return '\n'.join([str(r) for r in self])

    def create(self, name):
        """
        Add a project under name to the sheet.
        """
        self.sheet[name] = Project(name)

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
        for project in j.keys():
            self.create(project)
            for attr in ('notes','url','path','archive','datamap'):
                if attr in j[project]:
                    setattr(self.sheet[project], attr, j[project][attr])
                    j[project].pop(attr)
            for date in j[project]:
                hours = decimal.Decimal(j[project][date])
                self.sheet[project].add(hours, date)
        return self

    def tojson(self):
        """
        Converts the sheet to a JSON-compatible object.
        """
        j = dict()
        for project in self:
            j[project.title] = dict()
            for attr in ('notes','url','path','archive','datamap'):
                j[project.title][attr] = getattr(project, attr)
            for date,hours in project:
                j[project.title][date] = str(hours)
        return j

    def writejson(self, filename):
        """
        Exports projects and records to a JSON file.
        """
        with open(filename, 'w') as f:
            json.dump(self.tojson(), f, sort_keys=True)

class ProjectSheetIterable:
    def __init__(self, projectsheet):
        self.iterable = list(projectsheet.sheet.items())
        self.index = 0
    def __next__(self):
        try:
            key, value = self.iterable[self.index]
        except IndexError:
            raise StopIteration
        self.index += 1
        return value

if __name__ == '__main__':
    P = ProjectSheet().readjson('work.json')
    lastweek = datetime.datetime.today() - datetime.timedelta(days=7)
    print('This past week you have worked', str(P.since(lastweek)[0]), 'hours!')

