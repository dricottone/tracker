#!/usr/bin/python3
import sys, os.path
import sqlite3
import datetime     #for date data
import decimal      #for hours data
import json, pprint
import colorutils, dateutils, dirutils, termutils, sqlutils

COLWIDTH = 14
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

def db_create(filename):
    """
    Initializes database and calls CREATE TABLE.
    """
    connect, cursor = db_initialize(filename)
    cursor.execute("""CREATE TABLE tracker
                        (date text, name text, hours decimal)""")
    cursor.commit()
    return (cunnect, cursor)

# ^ Functions
###############################################################################
# v Classes

class TrackerDB():
    def __init__(self, filename):
        self.load_existing = False
        if os.path.isfile(filename):
            res = db_initialize(filename)
        else:
            res = db_create(filename)
        self.connect, self.cursor = res
    def __enter__(self):
        return self.cursor
    def __exit__(self):
        self.cursor.close()
        self.connect.close()

class TrackerInterface():
    def __init__(self, cursor):
        self.cursor = cursor
        self.projects = list()
        self.projects list_details(names=True, times=False)
    def list_details(self, names=True, times=True):
        self.cursor.execute("""SELECT name, SUM(time)
                                 FROM tracker
                                 GROUP BY name""")
        _projects = self.cursor.fetchone()
        #turn _projects to list, deleting indices based on kwargs
        return projects

    def search_details(self, pattern, names=True, times=True):
        targets = list_details(self, names=names, times=times)
        _pattern = re.compile(pattern)
        _matches = filter(_pattern.search(), targets)
        return _matches

    def add_time(self, project, time, date):
        #check that project exists
        self.cursor.execute("""INSERT INTO tracker (date, name, hours)
                                 VALUES (?,?,?)""", (date, project, time))
        self.cursor.commit()

    def remove_time(self, project, time, date):
        #check that project exists
        self.cursor.execute("""SELECT time FROM tracker
                                 WHERE project=? AND date=?""", (project, date))
        _time = self.cursor.fetchone()
        if _time is None:
            #couldn't find record?
        if _time <= time:
            self.cursor.execute("""DELETE FROM tracker
                                     WHERE project=? AND date=?""", (project, date))
            self.cursor.commit()
        else:
            self.cursor.execute("""UPDATE tracker
                                     SET time=?
                                     WHERE project=? AND date=?""", (_time - time, project, date))
            self.cursor.commit()
                                     
class Project:
    """
    Class for a project. Contains all component data as attributes.

    Is iterable over tuples of (date, hours) pairs.
    """
    def __init__(self, title):
        self.title = title
        self.time = decimal.Decimal()
        self.records = dict()

    def __iter__(self):
        return ProjectIterable(self)
    def __str__(self):
        return pprint.pformat(self.records)

    def add(self, hours, date=None, *, autowrite=False):
        """
        Adds a record with hours under date.
        """
        if date is None:
            date = getrecorddate()
        if date in self.records:
            self.records[date] += decimal.Decimal(hours)
        else:
            self.records[date] = decimal.Decimal(hours)
        self.time += decimal.Decimal(hours)

    def remove(self, hours, date=None, *, autowrite=False):
        """
        Subtracts hours from a record.
        """
        neghours = 0 - decimal.Decimal(hours)
        self.add(neghours, date, autowrite=autowrite)
        if self.records[date] <= 0:
            self.records.pop(date)

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
    def __init__(self, filename=None):
        self.filename = filename
        self.sheet = dict()
        self.index = 0

        if self.filename is not None:
            self.readjson(self.filename)

    def __iter__(self):
        return ProjectSheetIterable(self)
    def __str__(self):
        return '\n'.join([str(r) for r in self])

    def create(self, name, *, autowrite=False):
        """
        Add a project under name to the sheet.
        """
        self.sheet[name] = Project(name)
        if autowrite:
            result = self.writejson(self.filename)
        else:
            result = 0
        return result

    def add(self, name, hours, date, *, autowrite=False):
        """
        Interface for Project.add
        """
        self.sheet[name].add(hours, date)
        if autowrite:
            result = self.writejson(self.filename)
        else:
            result = 0
        return result

    def remove(self, name, hours, date, *, autowrite=False):
        """
        Interface for Project.remove
        """
        self.sheet[name].remove(hours, date)
        if autowrite:
            result = self.writejson(self.filename)
        else:
            result = 0
        return result

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
        try:
            with open(filename, 'r') as f:
                j = json.load(f)
        except IOError:
            return None
        for project in j.keys():
            self.create(project)
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
            for date,hours in project:
                j[project.title][date] = str(hours)
        return j

    def writejson(self, filename):
        """
        Exports projects and records to a JSON file.
        """
        try:
            with open(filename, 'w') as f:
                json.dump(self.tojson(), f, sort_keys=True)
        except IOError:
            return 1
        return 0

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
        self.week = tuple(dateutils.get_week(refdate))
        self.blocks = list()
        self.source = projectsheet
        self.colors = colorutils.highlighter(colorutils.SET_HIAA)
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
        return '\n'.join([str(self), buffer])

    def getcolor(self):
        return next(self.colors)

    def buildblock(self, date):
        block = list()
        crit_indices = list()
        for project in self.source:
            if date not in project.records:
                continue
            hours = project.records[date]
            crit_indices.append(len(block))
            block.extend( self.buildblockstub(project.title, hours) )
        length = len(block)
        diff = 8 - length
        if diff < 0:
            noncrit_indices = set(range(length)) - set(crit_indices)
            remove_indices = sorted(list(noncrit_indices), reverse=True)
            for index in remove_indices[:-diff]:
                block.pop(index)
        elif diff > 0:
            block.extend([FILL] * diff)
        return block

    def buildblockstub(self, name, hours):
        color = self.getcolor()
        text = ' '.join([name, ':', str(hours)])
        project_stubs = [color + text.ljust(COLWIDTH) + colorutils.RESET]
        spillover = ''.join([color, FILL, colorutils.RESET])
        hoursleft = round(hours) - 1
        for _ in range(hoursleft):
            project_stubs.append(spillover)
        return project_stubs

# ^ Classes
###############################################################################
# v CLI

def mainDisplay(projectsheet, weeksago):
    today = datetime.datetime.today()
    multiplier = int(weeksago) * 7
    someweeksago = today - datetime.timedelta(days=multiplier)
    S = ProjectSheetScreen(projectsheet, someweeksago)
    return (0, S.build())

def mainCreate(projectsheet, projectname):
    result = projectsheet.create(projectname, autowrite=True)
    return (result, {0: '', 1: 'Error in file IO'}[result])

def mainAdd(projectsheet, projectname, hours, daysago):
    today = datetime.datetime.today()
    date = today - datetime.timedelta(days=int(daysago))
    recorddate = getrecorddate(date)
    if projectname not in projectsheet.sheet:
        return (1, 'Project not in sheet') #otherwise will create project
    projectsheet.add(projectname, hours, recorddate, autowrite=True)
    return (0, '')

def mainRemove(projectsheet, projectname, hours, daysago):
    today = datetime.datetime.today()
    date = today - datetime.timedelta(days=int(daysago))
    recorddate = getrecorddate(date)
    if projectname not in projectsheet.sheet:
        return (1, 'Project not in sheet')
    projectsheet.remove(projectname, hours, recorddate, autowrite=True)
    return (0, '')

def mainInfo(projectsheet):
    return (0, 'Using data file at ' + P.filename)

def mainList(projectsheet):
    lines = list()
    for project in projectsheet:
        lines.append(project.title + '\t' + str(project.time))
    buffer = '\n'.join(lines)
    return (0, buffer)

mainfuncs = {'display': mainDisplay,
             'create': mainCreate,
             'add': mainAdd,
             'remove': mainRemove,
             'info': mainInfo,
             'list': mainList
            }

if __name__ == '__main__':
    global EXITCODE
    EXITCODE = 0
    dbfile = os.path.join(dirutils.findbasedir(), 'tracker', 'sheet.json')
    try:
        func = sys.argv[1]
        args = sys.argv[2:]
    except KeyError:
        termutils.errorp('Not a valid function: ', sys.argv[1])
    try:
        with TrackerDB(trackerdb) as tdb:
            res = mainfuncs[func](tdb, *args)
    except sqlite3.Error:
        termutils.errorp('Internal database error')
    if len(res):
        sys.stdout.write(res + '\n')
    sys.exit(EXITCODE)

