#!/usr/bin/env python
# encoding: utf-8

"""
ti is a simple and extensible time tracker for the command line. Visit the
project page (http://ti.sharats.me) for more details.

Usage:
  ti (o|on) <name> [<time>...]
  ti (f|fin) [<time>...]
  ti (s|status)
  ti (t|tag) <tag>...
  ti (n|note) <note-text>...
  ti (l|log) [today]
  ti (e|edit)
  ti (i|interrupt)
  ti --no-color
  ti -h | --help

Options:
  -h --help         Show this help.
  <start-time>...   A time specification (Go to http://ti.sharats.me for more on
                    this).
  <tag>...          Tags can be made of any characters, but its probably a good
                    idea to avoid whitespace.
  <note-text>...    Some arbitrary text to be added as `notes` to the currently
                    working project.
"""

from __future__ import print_function
from __future__ import unicode_literals

#  import pytz
import json, yaml
from datetime import datetime, timedelta, date
from collections import defaultdict
import re
import os, subprocess, tempfile
from os import path
import sys
import subprocess
import math
import ConfigParser
import StringIO
import parsedatetime
#  import shlex #may not be there on Windows

from colorama import *

class JsonStore(object):

    def __init__(self):
        cfg_fname = os.path.abspath(os.path.expanduser('~/.tim.ini'))
        self.cfg = ConfigParser.SafeConfigParser() 

        self.cfg.add_section('tim')
        self.cfg.set('tim', 'folder', os.path.abspath(os.path.expanduser('~')))
        self.cfg.read(cfg_fname)  #no error if not found
        self.filename = os.path.abspath(os.path.join(self.cfg.get('tim','folder'), 'tim-sheet.json'))
        print("self.filename: %s" % (self.filename))

    def load(self):

        if path.exists(self.filename):
            with open(self.filename) as f:
                data = json.load(f)

        else:
            data = {'work': [], 'interrupt_stack': []}

        return data

    def dump(self, data):
        with open(self.filename, 'w') as f:
            json.dump(data, f, separators=(',', ': '), indent=2)


def red(str):
    if use_color:
        return Fore.RED + str + Fore.RESET
    else:
        return str

def green(str):
    if use_color:
        return Fore.GREEN + str + Fore.RESET
    else: 
        return str

def yellow(str):
    if use_color: 
        return Fore.YELLOW + str + Fore.RESET
    else:
        return str

def blue(str):
    if use_color: 
        return Fore.BLUE + str + Fore.RESET
    else:
        return str

def bold(str):
#doesn't do much on my ConEmu Windows 7 system, but let's see
    if use_color:
        return Style.BRIGHT + str + Style.RESET_ALL
    else:
        return str

def action_switch(name, time):
    action_end(time)
    action_begin(name, time)

def action_begin(name, time):
    data = store.load()
    work = data['work']

    if work and 'end' not in work[-1]:
        print('You are already working on ' + yellow(work[-1]['name']) +
                '. Stop it or use a different sheet.', file=sys.stderr)
        raise SystemExit(1)

    entry = {
        'name': name,
        'start': time,
    }

    work.append(entry)
    store.dump(data)

    print('Start working on ' + green(name) + ' at ' + time + '.')


def action_end(time, back_from_interrupt=True):
    ensure_working()

    data = store.load()

    current = data['work'][-1]
    current['end'] = time

    start_time = parse_isotime(current['start'])
    diff = timegap(start_time, datetime.utcnow())
    print('You stopped working on ' + red(current['name']) + ' at ' + time + ' (total: ' + bold(diff) + ').')
    store.dump(data)

def action_status():
    try:
        ensure_working()
    except SystemExit(1):
        return

    data = store.load()
    current = data['work'][-1]

    start_time = parse_isotime(current['start'])
    diff = timegap(start_time, datetime.utcnow())

    print('You have been working on {0} for {1}.'
            .format(green(current['name']), diff))

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
    print("#I suggest you call tim ini > ~/.tim.ini to start using this optional config file")

    print(out_str.getvalue())

#  def action_edit():
#      if 'EDITOR' not in os.environ:
#          print("Please set the 'EDITOR' environment variable", file=sys.stderr)
#          raise SystemExit(1)
#  
#      data = store.load()
#      yml = yaml.safe_dump(data, default_flow_style=False, allow_unicode=True)
#  
#      cmd = os.getenv('EDITOR')
#      fd, temp_path = tempfile.mkstemp(prefix='ti.')
#      with open(temp_path, "r+") as f:
#          f.write(yml.replace('\n- ', '\n\n- '))
#          f.seek(0)
#          subprocess.check_call(cmd + ' ' + temp_path, shell=True)
#          yml = f.read()
#          f.truncate()
#          f.close
#  
#      os.close(fd)
#      os.remove(temp_path)
#  
#      try:
#        data = yaml.load(yml)
#      except:
#        print("Oops, that YAML didn't appear to be valid!", file=sys.stderr)
#        raise SystemExit(1)
#  
#      store.dump(data)
#  

def is_working():
    data = store.load()
    return data.get('work') and 'end' not in data['work'][-1]


def ensure_working():
    if is_working(): return

    print("For all I know, you aren't working on anything."
            " I don't know what to do.", file=sys.stderr)
    print('See `ti -h` to know how to start working.', file=sys.stderr)
    raise SystemExit(1)


def to_datetime(timestr):
    #Z denotes zulu for UTC (https://tools.ietf.org/html/rfc3339#section-2)
    dt = parse_engtime(timestr).isoformat() + "Z" 
    return dt

def parse_engtime(timestr):
#http://stackoverflow.com/questions/4615250/python-convert-relative-date-string-to-absolute-date-stamp
    cal = parsedatetime.Calendar()
    if timestr is None or timestr is "":\
        timestr = 'now'

    #example from here: https://github.com/bear/parsedatetime/pull/60
    ret = cal.parseDT(timestr, sourceTime=datetime.utcnow())[0]
    return ret
    # interim_result = cal.parse(timestr)
    
    # return datetime.datetime(*interim_result[0][:6])
    
def parse_engtime_old(timestr):
    now = datetime.utcnow().replace(microsecond=0)
    # print("now", now, now.tzinfo)
    if not timestr or timestr.strip() == 'now':
        return now

    match = re.match(r'(\d+|a) \s* (s|secs?|seconds?) \s+ ago $', timestr, re.X)
    if match is not None:
        n = match.group(1)
        seconds = 1 if n == 'a' else int(n)
        return now - timedelta(seconds=seconds)

    match = re.match(r'(\d+|a) \s* (mins?|minutes?) \s+ ago $', timestr, re.X)
    if match is not None:
        n = match.group(1)
        minutes = 1 if n == 'a' else int(n)
        return now - timedelta(minutes=minutes)

    match = re.match(r'(\d+|a|an) \s* (hrs?|hours?) \s+ ago $', timestr, re.X)
    if match is not None:
        n = match.group(1)
        hours = 1 if n in ['a', 'an'] else int(n)
        return now - timedelta(hours=hours)

    raise ValueError("Don't understand the time '" + timestr + "'")


def parse_isotime(isotime):
    return datetime.strptime(isotime, '%Y-%m-%dT%H:%M:%SZ')


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
        return "more than a day " + red("(%d hours)" %(hours))
    # elif mins < 43199:
    #     return 'about {} days'.format(mins / 1440)
    # elif mins < 86399:
    #     return 'about a month'
    # elif mins < 525599:
    #     return 'about {} months'.format(mins / 43200)
    # else:
    #     return 'more than a year'


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

    #  elif head in ['e', 'edit']:
    #      fn = action_edit
    #      args = {}

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
            helpful_exit('Need the name of whatever you are working on.')

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

    elif head in ['ini']:
        fn = action_ini
        args = {}
    else:
        helpful_exit("I don't understand '" + head + "'")

    return fn, args


def main():
    fn, args = parse_args()
    fn(**args)


store = JsonStore()
use_color = True

if __name__ == '__main__':
    main()
