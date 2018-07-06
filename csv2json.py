#!/usr/bin/env python3
import json, csv, sys
from tracker import getrecorddate
from dateutils import fromAmerican

def main(infile, outfile):
    """
    Converts a CSV file into a JSON file.
    Assumes first row is the unique identifier, and that the header row is
    dates writen as MM/DD/YYYY.
    """
    with open(infile, 'r') as i:
        reader = csv.DictReader(i)
        sheet = dict()
        for line in reader:
            row = list(line.items())
            uid, records = row[0][1], row[1:]
            sheet[uid] = dict()
            for key, value in records:
                if not len(value):
                    continue
                sheet[uid][getrecorddate(fromAmerican(key))] = value
        with open(outfile, 'w') as o:
            json.dump(sheet, o, sort_keys=True)

if __name__ == '__main__':
    if len(sys.argv[1:]) < 2:
        sys.exit(1)
    infile = sys.argv[1]
    outfile = sys.argv[2]
    main(infile, outfile)

