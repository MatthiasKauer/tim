#!/usr/bin/env python
# encoding: utf-8

from __future__ import print_function
from __future__ import unicode_literals

import sys
from datetime import datetime, timedelta, date
from collections import defaultdict
import os
import subprocess
import math
import ConfigParser
import StringIO
import shutil
import json, yaml

import pytz
import parsedatetime
# http://stackoverflow.com/questions/13218506/how-to-get-system-timezone-setting-and-pass-it-to-pytz-timezone
from tzlocal import get_localzone # $ pip install tzlocal
local_tz = get_localzone()

from tim import __version__
from tim.coloring import TimColorer

date_format = '%Y-%m-%dT%H:%M:%SZ'

class JsonStore(object):
    """handles time log in json form"""

    def __init__(self):
        cfg_fname = os.path.abspath(os.path.expanduser('~/.tim.ini'))
        self.cfg = ConfigParser.SafeConfigParser() 

        self.cfg.add_section('tim')
        self.cfg.set('tim', 'folder', os.path.abspath(os.path.expanduser('~')))
        self.cfg.set('tim', 'editor', "vim")
        self.cfg.read(cfg_fname)  #no error if not found
        self.filename = os.path.abspath(os.path.join(self.cfg.get('tim','folder'), 'tim-sheet.json'))
        print("#self.filename: %s" % (self.filename))

    def load(self):
        """read from file"""
        if os.path.exists(self.filename):
            with open(self.filename) as f:
                data = json.load(f)

        else:
            data = {'work': [], 'interrupt_stack': []}

        return data

    def dump(self, data):
        """write data to file"""
        with open(self.filename, 'w') as f:
            json.dump(data, f, separators=(',', ': '), indent=2)


def action_switch(name, time):
    action_end(time)
    action_begin(name, time)


def action_begin(name, time):
    data = store.load()
    work = data['work']

    if work and 'end' not in work[-1]:
        print('You are already working on ' + tclr.yellow(work[-1]['name']) +
                '. Stop it or use a different sheet.', file=sys.stderr)
        raise SystemExit(1)

    entry = {
        'name': name,
        'start': time,
    }

    work.append(entry)
    store.dump(data)

    print('Start working on ' + tclr.green(name) + ' at ' + time + '.')


def action_printtime(time):
    print("You entered '" + time + "' as a test")


def action_end(time, back_from_interrupt=True):
    ensure_working()

    data = store.load()

    current = data['work'][-1]
    current['end'] = time

    start_time = parse_isotime(current['start'])
    # print(type(start_time), type(time))
    diff = timegap(start_time, parse_isotime(time))
    print('You stopped working on ' + tcrl.red(current['name']) + ' at ' + time + ' (total: ' + tclr.bold(diff) + ').')
    store.dump(data)


def action_status():
    ensure_working()
    # except SystemExit(1):
    #     return

    data = store.load()
    current = data['work'][-1]

    start_time = parse_isotime(current['start'])
    diff = timegap(start_time, datetime.utcnow())

    print('You have been working on {0} for {1}.'
            .format(tclr.green(current['name']), diff))


def action_hledger(param):
    # print("hledger param", param)
    data = store.load()
    work = data['work']

    # hlfname = os.path.expanduser('~/.tim.hledger')
    hlfname = os.path.join( store.cfg.get('tim', 'folder'), '.tim.hledger-temp')
    hlfile = open(hlfname, 'w')

    for item in work:
        if 'end' in item:
            str_on = "i %s %s" % (parse_isotime(item['start']), item['name'])
            str_off = "o %s" % (parse_isotime(item['end']))
            # print(str_on + "\n" + str_off)

            hlfile.write(str_on + "\n")
            hlfile.write(str_off + "\n")
            #  hlfile.write("\n")

    hlfile.close()

    cmd_list = ['hledger'] + ['-f'] + [hlfname] + param
    print("tim executes: " + " ".join(cmd_list))
    subprocess.call(cmd_list) 


def action_ini():
    out_str = StringIO.StringIO()

    store.cfg.write(out_str)
    print("#this is the ini file for tim - a tiny time keeping tool with hledger in the back")
    print("#I suggest you call tim ini > %s to start using this optional config file"
            %(os.path.abspath(os.path.expanduser('~/.tim.ini'))))

    print(out_str.getvalue())


def action_version():
    print("tim version " + __version__)


def action_edit():
    editor_cfg = store.cfg.get('tim', 'editor')
    print(editor_cfg)
    if 'EDITOR' in os.environ:
        cmd = os.getenv('EDITOR')
    if editor_cfg is not "":
        cmd = editor_cfg
    else:
        print("Please set the 'EDITOR' environment variable or adjust editor= in ini file", file=sys.stderr)
        raise SystemExit(1)

    bakname = os.path.abspath(store.filename + '.bak-' + date.today().strftime("%Y%m%d"))
    shutil.copy(store.filename, bakname)
    print("Created backup of main sheet at " + bakname + ".")
    print("You must delete those manually! Now begin editing!")
    subprocess.check_call(cmd + ' ' + store.filename, shell=True)
 

def ensure_working():
    data = store.load()
    work_data = data.get('work') 
    is_working = work_data and 'end' not in data['work'][-1]
    if is_working:
        return True

    # print(has_data)
    if work_data:
        last = work_data[-1]
        print("For all I know, you last worked on {} from {} to {}".format(
                tclr.blue(last['name']), tclr.green(last['start']), tcrl.red(last['end'])),
                file=sys.stderr)
        # print(data['work'][-1])
    else:
        print("For all I know, you " + tclr.bold("never") + " worked on anything."
            " I don't know what to do.", file=sys.stderr)

    print('See `ti -h` to know how to start working.', file=sys.stderr)
    raise SystemExit(1)


def to_datetime(timestr):
    #Z denotes zulu for UTC (https://tools.ietf.org/html/rfc3339#section-2)
    # dt = parse_engtime(timestr).isoformat() + "Z" 
    dt = parse_engtime(timestr).strftime(date_format)
    return dt


def parse_engtime(timestr):
#http://stackoverflow.com/questions/4615250/python-convert-relative-date-string-to-absolute-date-stamp
    cal = parsedatetime.Calendar()
    if timestr is None or timestr is "":\
        timestr = 'now'

    #example from here: https://github.com/bear/parsedatetime/pull/60
    ret = cal.parseDT(timestr, tzinfo=local_tz)[0]
    ret_utc = ret.astimezone(pytz.utc)
    # ret = cal.parseDT(timestr, sourceTime=datetime.utcnow())[0]
    return ret_utc
    

def parse_isotime(isotime):
    return datetime.strptime(isotime, date_format )


def timegap(start_time, end_time):
    diff = end_time - start_time

    mins = math.floor(diff.seconds / 60)
    hours = math.floor(mins/60)
    rem_mins = mins - hours * 60

    if mins == 0:
        return 'under 1 minute'
    elif mins < 59:
        return '%d minutes' % (mins)
    elif mins < 1439:
        return '%d hours and %d minutes' % (hours, rem_mins)
    else:
        return "more than a day " + tcrl.red("(%d hours)" %(hours))
   

def helpful_exit(msg=__doc__):
    print(msg, file=sys.stderr)
    raise SystemExit


def parse_args(argv=sys.argv):
    global use_color

    argv = [arg.decode('utf-8') for arg in argv]

    if '--no-color' in argv:
        use_color = False
        argv.remove('--no-color')

    # prog = argv[0]
    if len(argv) == 1:
        helpful_exit('You must specify a command.')

    head = argv[1]
    tail = argv[2:]
      
    if head in ['-h', '--help', 'h', 'help']:
        helpful_exit()

    elif head in ['e', 'edit']:
        fn = action_edit
        args = {}

    elif head in ['bg', 'begin','o', 'on']:
        if not tail:
            helpful_exit('Need the name of whatever you are working on.')

        fn = action_begin
        args = {
            'name': tail[0],
            'time': to_datetime(' '.join(tail[1:])),
        }

    elif head in ['sw', 'switch']:
        if not tail:
            helpful_exit('I need the name of whatever you are working on.')

        fn = action_switch
        args = {
            'name': tail[0],
            'time': to_datetime(' '.join(tail[1:])),
        }

    elif head in ['f', 'fin', 'end', 'nd']:
        fn = action_end
        args = {'time': to_datetime(' '.join(tail))}

    elif head in ['st', 'status']:
        fn = action_status
        args = {}

    elif head in ['l', 'log']:
        fn = action_log
        args = {'period': tail[0] if tail else None}

    elif head in ['hl', 'hledger']:
        fn = action_hledger
        args = {'param': tail}

    elif head in ['hl1']:
        fn = action_hledger
        args = {'param': ['balance', '--daily','--begin', 'today'] + tail}
    
    elif head in ['hl2']:
        fn = action_hledger
        args = {'param': ['balance', '--daily','--begin', 'this week'] + tail}

    elif head in ['hl3']:
        fn = action_hledger
        args = {'param': ['balance', '--weekly','--begin', 'this month'] + tail}

    elif head in ['hl4']:
        fn = action_hledger
        args = {'param': ['balance', '--monthly','--begin', 'this year'] + tail}

    elif head in ['ini']:
        fn = action_ini
        args = {}

    elif head in ['--version', '-v']:
        fn = action_version
        args = {}

    elif head in ['pt', 'printtime']:
        fn = action_printtime
        args = {'time': to_datetime(' '.join(tail))}
    else:
        helpful_exit("I don't understand command '" + head + "'")

    return fn, args


def main():
    fn, args = parse_args()
    fn(**args)


store = JsonStore()
tclr = TimColorer(use_color=True)
# use_color = True

if __name__ == '__main__':
    main()
