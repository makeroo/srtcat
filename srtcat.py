#!/usr/bin/python -u

'''
Created on 14/mar/2013

@author: makeroo
'''

import sys
import re
import argparse

shiftFormat = re.compile(r'^\#?\d+(:\d+)?(:\d+)?(,\d+)?$')
strIndexLine = re.compile(r'^\d+$')
strTimeLine = re.compile(r'^(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})$')

def strTime (seconds):
    micros = (seconds * 1000) % 1000
    seconds = int(seconds)
    secs = seconds % 60
    seconds = seconds / 60
    mins = seconds % 60
    hours = seconds / 60
    return '%02d:%02d:%02d,%03d' % (hours, mins, secs, micros)

def lineTime (f, t):
    return '%s --> %s' % (strTime(f), strTime(t))

def trimEndingNewline (line):
    while len(line) and line[-1] in ('\n', '\r'):
        line = line[:-1]
    return line

class SrtCat (object):
    def do (self, inputs, output, amount):
        self.toTime = 0
        self.amount = amount
        self.out = output
        self.file = 1
        self.line = 1
        self.state = self._lineIndex
        self.copy = False
        for srtFile in inputs:
            self.curline = 0
            self._shift(srtFile)
            self.amount += self.toTime
            self.file += 1

    def _shift (self, srtFile):
        while True:
            line = srtFile.readline()
            self.curline += 1
            if len(line) == 0:
                break
            self.state(trimEndingNewline(line))

    def _lineIndex (self, line):
        if not strIndexLine.match(line):
            print >> sys.stderr, 'file %s, line %s: format error, expecting index line, found: ##%s##' % (self.file, self.curline, line)
        else:
            self.state = self._lineTime

    def _lineTime (self, line):
        m = strTimeLine.match(line)
        if not m:
            print >> sys.stderr, 'file %s, line %s: format error, expecting time line, found: ##%s##' % (self.file, self.curline, line)
        else:
            f = parseShift(m.group(1), False) + self.amount
            t = parseShift(m.group(2), False) + self.amount
            if t > self.toTime:
                self.toTime = t
            elif t > 0:
                print >> sys.stderr, 'file %s, line %s: time error, expecting %s, found %s' % (self.file, self.curline, strTime(self.toTime), strTime(t))
            self.copy = f >= 0 and t >= 0
            if self.copy:
                print >> self.out, self.line
                self.line += 1
                print >> self.out, lineTime(f, t)
            self.state = self._lineText

    def _lineText (self, line):
        if self.copy:
            print >> self.out, line
        if len(line) == 0:
            self.state = self._lineIndex

def parseShift (s, check=True):
    if check and not shiftFormat.match(s):
        return 0
    o = 1
    if s.startswith('#'):
        o = -1
        s = s[1:]
    p = s.split(':')
    if len(p) == 1:
        return o * float(s)
    j = 1.0
    v = 0
    for k in reversed(p):
        v += float(k.replace(',', '.')) * j
        j *= 60.0
    return v * o

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Join srt files')
    parser.add_argument('files', metavar='SRT', type=argparse.FileType('r'), nargs='+', default=sys.stdin,
                        help='srt input files')
    parser.add_argument('-o', '--output', dest='out', type=argparse.FileType('w'), nargs='?', default=sys.stdout,
                        help='output file (default stdout)')
    parser.add_argument('--shift', dest='shift', type=str, nargs='?', default='0',
                        help='add/subtract time to subtitles. Format: seconds or hh:mm:ss,micros')
    args = parser.parse_args()
    SrtCat().do(args.files, args.out, parseShift(args.shift))
