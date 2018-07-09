#!/usr/bin/python3
import datetime, json, decimal, pprint
import colorutils, dateutils

COLWIDTH = 10
FILL = ' ' * COLWIDTH

# ^ Constants
###############################################################################
# v Functions

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

# ^ Functions
###############################################################################
# v Classes

class Project:
    """
    Class for a project. Contains all component data as attributes.

    Is iterable over tuples of (date, hours) pairs.
    """
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
    """
    Implementation of iteration for the Project class.
    """
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
    """
    Container for projects. Offers methods for operating on all projects.
    """
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
    """
    Implementation of iteration for the ProjectSheet class.
    """
    def __init__(self, projectsheet):
        self.iterable = sorted(list(projectsheet.sheet.items()),
                               key=lambda x: x[1].title)
        self.index = 0
    def __next__(self):
        try:
            key, value = self.iterable[self.index]
        except IndexError:
            raise StopIteration
        self.index += 1
        return value

class ProjectSheetScreen:
    """
    Class for building up a printable sheet.
    """
    def __init__(self, projectsheet, refdate):
        self.week = dateutils.getweek(refdate)
        self.blocks = list()
        self.source = projectsheet
        self.colors = colorutils.highlighter(colorutils.HIAA_BACK_BLACKFORE)
    def __str__(self):
        return 'The week starting on {} {}:'.format( \
            dateutils.MONTHS_SHORT[self.week[0].month], self.week[0].day)

    def build(self):
        self.blocks = list()
        for date in self.week:
            date = getrecorddate(date)
            self.blocks.append( self.buildblock(date) )
        buffer = ''.join(d.ljust(COLWIDTH) for d in dateutils.WEEKDAYS) + '\n'
        for line in zip(*self.blocks):
            buffer = ''.join([buffer, ''.join(line), '\n'])
        return buffer

    def getcolor(self):
        return next(self.colors)

    def buildblock(self, date):
        block = list()
        crit_indices = list()
        for project in self.source:
            if date not in project.records:
                continue
            hours = round(project.records[date])
            crit_indices.append(len(block))
            block.extend( self.buildblockstub(project.title, hours) )
        length = len(block)
        diff = 8 - length
        if diff < 0:
            spillover_indices = [i for i in range(length) not in crit_indices]
            for index in spillover_indices[:diff:-1]:
                block.pop(index)
        elif diff > 0:
            block.extend([FILL] * diff)
        return block

    def buildblockstub(self, name, hours):
        color = self.getcolor()
        project_stubs = [color + name.ljust(COLWIDTH) + colorutils.RESET]
        spillover = ''.join([color, FILL, colorutils.RESET])
        for _ in range(hours-1):
            project_stubs.append(spillover)
        return project_stubs

# ^ Classes
###############################################################################
# v Main

if __name__ == '__main__':
    today = datetime.datetime.today()
    lastweek = today - datetime.timedelta(days=7)
    P = ProjectSheet().readjson('work.json')
    S = ProjectSheetScreen(P, today)
    print(S)
    print(S.build())

