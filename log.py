#!/usr/bin/env python2
# coding=utf-8
import inspect
import os

class Logger():
    def __init__(self, io = None, 
            save_log = True, 
            save_warnings = True,
            save_debug = False, 
            save_errors = True):
        
        self.io = io
        
        self.save_log = save_log
        self.save_warnings = save_warnings
        self.save_debug = save_debug
        self.save_errors = save_errors

        self.everything = []

    def _dump_line(self, msg_tuple):
        frame,filename,line_number,function_name,lines,index=\
            inspect.getouterframes(inspect.currentframe())[2]

        filename = os.path.split(filename)[1]

        line = "%s:%d at %s() \t[%s] %s\n" % \
            (filename, line_number, function_name, msg_tuple[0], msg_tuple[1])
        io = self.io
        if not self.io is None:
            self.io.write(line)
        

    def log(self, msg):
        if not(self.save_log):
            return

        msg_tuple = ("Log", msg)
        self.everything.append(msg_tuple)
        self._dump_line(msg_tuple)

    def warn(self, msg):
        if not(self.save_warnings):
            return

        msg_tuple = ("Warn", msg)
        self.everything.append(msg_tuple)
        self._dump_line(msg_tuple)

    def error(self, msg):
        if not(self.save_errors):
            return

        msg_tuple = ("Error", msg)
        self.everything.append(msg_tuple)
        self._dump_line(msg_tuple)

    def debug(self, msg):
        if not(self.save_debug):
            return

        msg_tuple = ("Debug", msg)
        self.everything.append(msg_tuple)
        self._dump_line(msg_tuple)
       
    def dump_s(self):
        out = ""
        for logtype, line in self.everything:
            line = "[%s] %s\n" % (logtype, line) 
            out += line

    def dump(self, io):
        io.write(self.dump_s())
