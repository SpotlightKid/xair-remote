#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# xaircmd.py
#
"""Simple X-AIR mixer debugging REPL."""

from __future__ import division, print_function, unicode_literals

import argparse
import ast
import csv
import logging
import queue
import shlex
import sys

from collections import namedtuple
from os.path import dirname, expanduser, join

import cmd2 as cmd
from colorama import Fore
from liblo import ServerThread


log = logging.getLogger('xaircmd')

XAirCommand = namedtuple('XAirCommand', 'address,types,range,values,description'.split(','))


def parse_commands(filename='xair-cmdlist.csv'):
    commands = dict()
    with open(join(dirname(__file__), filename), newline='') as csvfile:
        reader = csv.reader(csvfile, delimiter=',', strict=True)
        try:
            for i, row in enumerate(reader):
                if i == 0 and tuple(row) == XAirCommand._fields:
                    continue
                try:
                    commands[row[0]] = XAirCommand(*row)
                except TypeError:
                    log.warn("Invalid command in '%s', line %i: %r", filename, i, row)
        except csv.Error as exc:
            log.error("Error in command file '%s', line %i: %s", filename, i, exc)
    return commands


class XAirCmdApp(cmd.Cmd):
    allow_cli_args = False
    abbrev = True
    intro = "Enter OSC command (Control-C or Control-D to quit)..."
    prompt = 'xair> '
    # legalChars = u'/' + cmd.Cmd.legalChars

    def __init__(self, server, destport=10024, srcport=11111, debug=False, **kwargs):
        """Class initialiser."""
        self.timeout = self.settable['timeout'] = 500
        self.server = self.settable['server'] = server
        self.destport = self.settable['destport'] = destport
        # add built-in custom command shortcuts
        self.shortcuts.update({
            '/': 'osc',
        })
        # add built-in custom command aliases
        kwargs.setdefault('use_ipython', True)
        super().__init__(**kwargs)
        self.aliases.update({
            'mute': 'osc /lr/mix/on 0',
            'unmute': 'osc /lr/mix/on 1',
            'mainvol': '/lr/mix/fader',
        })
        self.srcport = srcport
        self.debug = debug
        self.osc_commands = parse_commands()
        self.osc_command_names = sorted([cmd.address.lstrip('/')
                                         for cmd in self.osc_commands.values()])
        self.queue = queue.Queue()
        self.osc = ServerThread(self.srcport)
        self.osc.add_method(None, None, self.osc_recv)

        # hooks
        self.register_preloop_hook(self.start_osc_server)
        self.register_postloop_hook(self.stop_osc_server)

    def osc_recv(self, path, args, types, addr):
        log.debug("OSC RECV (%s, %s): %s %s [%s]", addr.hostname, addr.port, path,
                  types, ", ".join(repr(arg) for arg in args))
        self.queue.put((path, args, types, addr))

    def do_osc(self, line):
        if not line:
            return self.help_osc()

        try:
            oscaddr, rawargs = line.split(None, 1)
        except ValueError:
            oscaddr = line
            rawargs = ''

        oscaddr = '/' + oscaddr.lstrip('/')
# ~        if not oscaddr.startswith('/'):
# ~            self.perror("OSC address must start with a slash", traceback_war=False)
# ~            return

        oscargs = []
        for arg in shlex.split(rawargs, posix=False):
            if arg.strip():
                try:
                    oscargs.append(ast.literal_eval(arg))
                except:  # noqa:E722
                    oscargs.append(arg)

        log.debug("OSC SEND -> (%s, %s): %s %s", self.server, self.destport, oscaddr,
                  "".join("%r" % arg for arg in oscargs))
        self.osc.send((self.server, self.destport), oscaddr, *oscargs)

        try:
            path, args, types, addr = self.queue.get(timeout=self.timeout / 1000)
        except queue.Empty:
            self.p_warn("No reply within timeout ({:d} msec).".format(self.timeout))
        else:
            self.p_ok("{} {} [{}]".format(path, types, ", ".join(repr(arg) for arg in args)))

    def help_osc(self):
        self.poutput("osc ADDR [arg1 [arg2] ... [argn]]")

    def complete_osc(self, text, line, begidx, endidx):
        log.debug((text, line, begidx, endidx))

        #if not text.startswith('/'):
        #    text = '/' + text

        return self.delimiter_complete(text, line, begidx, endidx, self.osc_command_names, '/')

    def p_ok(self, msg):
        self.poutput(msg, color=Fore.GREEN)

    def p_warn(self, msg):
        self.poutput(msg, color=Fore.YELLOW)

    def start_osc_server(self) -> None:
        self.osc.start()

    def stop_osc_server(self) -> None:
        self.osc.stop()
        self.poutput('')

    def postparse(self, parse_result) -> None:
        log.debug("postparse: %r", list(parse_result))
        return parse_result


def main(args=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('-v', '--verbose', action="store_true",
                    help="Be verbose")
    ap.add_argument('-s', '--srcport', type=int, default=11111,
                    help="UDP source port of the client (default: %(default)s)")
    ap.add_argument('-p', '--destport', type=int, default=10024,
                    help="UDP destination port of the server (default: %(default)s)")
    ap.add_argument('server', metavar="ADDRESS", nargs='?', default="192.168.1.1",
                    help="Hostname or IP address of X-AIR's UDP server (default: %(default)s)")

    args = ap.parse_args(args if args is not None else sys.argv[1:])

    logging.basicConfig(format="%(levelname)s - %(message)s", filename="xaircmd.log",
                        level=logging.DEBUG if args.verbose else logging.INFO)

    app = XAirCmdApp(args.server, args.destport, args.srcport, args.verbose,
                     persistent_history_file=join(expanduser("~"), ".xaircmd_history"))
    return app.cmdloop()


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]) or 0)
