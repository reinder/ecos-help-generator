#
# HTML help generator for ESU Command Station (ECoS) network protocol
#
# Copyright (C) 2024 Reinder Feenstra
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

import socket
import os
import re


class ECoSHelpGenerator:
    """HTML help generator for ESU Command Station (ECoS) network protocol

    This generator connects to the ECoS and then uses help() commands to fetch
    all ECoSNet protocol documentation and generates HTML pages of it.

    See: <https://github.com/reinder/ecos-help-generator>
    """

    COMMANDS = ['get', 'set', 'create', 'delete', 'request', 'release', 'link',
                'unlink', 'queryObjects']

    def __init__(self, ip: str, output_dir: str, verbose: bool = False):
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.connect((ip, 15471))
        self._socket.settimeout(0.1)
        self._output_dir = output_dir
        self._verbose = verbose

    def build(self):
        """Build the HTML documentation."""
        os.makedirs(self._output_dir, 0o755, True)

        filename = 'index.html'
        nav = [('index', filename)]
        txt = self._request('help()')

        # generic:
        txt = re.sub(r'help\(([a-z]+)\)',
                     lambda m: self._build_generic_help(m.group(1), nav),
                     txt)

        # object classes:
        offset = txt.index('Implemented objectclasses:')
        txt = txt[:offset] + re.sub(r'^(\s+)([a-z-]+)\b',
                                    lambda m: m.group(1) + self._build_object_class_help(m.group(2), nav),
                                    txt[offset:], flags=re.MULTILINE)

        self._write_html(filename, 'Index', txt)

    def _build_generic_help(self, topic: str, nav: list):
        filename = topic + '.html'
        txt = self._request('help({:s})'.format(topic))
        self._write_html(filename, topic.capitalize(), txt, nav + [(topic, filename)])
        return '<a href="{:s}">help({:s})</a>'.format(filename, topic)

    def _build_object_class_help(self, object_class: str, nav: list):
        filename = object_class + '.html'
        txt = self._request('help({:s})'.format(object_class))

        # header:
        txt = re.sub(r'(Manager: \d+ \()([a-z-]+)(\))', r'\1<a href="\2.html">\2</a>\3', txt)

        # commands:
        for command in self.COMMANDS:
            response = self._request('help({:s},{:s})'.format(object_class, command))
            if response is not None:
                response = response[(response.index('Options for ' + command + ' command:')):]
                response = re.sub(r'^(\s{4})([a-z0-9-]+)\b',
                                  lambda m: m.group(1) + self._build_object_command_help(object_class, command, m.group(2), nav + [(object_class, filename)]),
                                  response, flags=re.MULTILINE)
                txt += os.linesep + '<a id="' + command + '"></a>' + response

        self._write_html(filename, object_class, txt, nav + [(object_class, filename)])
        return '<a href="{:s}">{:s}</a>'.format(filename, object_class)

    def _build_object_command_help(self, object_class: str, command: str, attribute: str, nav: list):
        filename = object_class + '.' + command + '.' + attribute + '.html'
        txt = self._request('help({:s},{:s},{:s})'.format(object_class, command, attribute))
        self._write_html(filename, '{:s} :: {:s} :: {:s}'.format(object_class, command, attribute), txt, nav + [(command, nav[-1][1] + '#' + command), (attribute, filename)])
        return '<a href="{:s}">{:s}</a>'.format(filename, attribute)

    def _request(self, command: str) -> str | None:
        """Send a request to the ECoS"""
        self._socket.send(command.encode('ascii'))
        response = bytes()
        try:
            while True:
                response += self._socket.recv(4096)
        except TimeoutError:
            pass
        response = response.decode('ascii')
        if not response.startswith('#'):
            return None
        response = re.sub(r'^#( |)', '', response, flags=re.MULTILINE)
        response = response.replace('<', '&lt;').replace('>', '&gt;')
        return response

    def _write_html(self, filename: str, title: str, text: str, nav: list = []):
        """Write HTML file to the output_dir"""
        with open(os.path.join(self._output_dir, filename), 'w') as f:
            f.write('''<!doctype html>
<html>
<head>
  <title>''' + title + ''' :: ECoSNet protocol documentation</title>
  <style>
    @media (prefers-color-scheme: dark)
    {
      body { background-color: #111; color: #eee; }
      a { color: rgb(47, 129, 247); }
      a:visited { color: #6F01EC; }
    }
  </style>
</head>
<body>
<pre>
''')
            if len(nav) > 1:
                for item in nav:
                    if item != nav[-1]:
                        f.write('<a href="' + item[1] + '">' + item[0] + '</a> &raquo; ')
                    else:
                        f.write(item[0])
                f.write(os.linesep + ('-' * 80) + os.linesep + os.linesep)

            f.write(text)
            f.write(os.linesep + ('-' * 80) + os.linesep + 'Generated using <a href="https://github.com/reinder/ecos-help-generator">ECoS help generator</a> - For personal use only!')
            f.write('</pre></body></html>')

        if self._verbose:
            print('Wrote: ' + filename)


if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print('Usage: {:s} <ecos_ip> [<output_dir]'.format(sys.argv[0]))
        print('  ecos_ip     IP address of ECoS')
        print('  output_dir  Directory for generated files, defaults to: output')
        sys.exit(1)

    ecos_help = ECoSHelpGenerator(sys.argv[1], sys.argv[2] if len(sys.argv) >= 3 else 'output', verbose=True)
    ecos_help.build()
