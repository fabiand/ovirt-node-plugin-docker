#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# docker_page.py - Copyright (C) 2012 Red Hat, Inc.
# Written by Fabian Deutsch <fabiand@redhat.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
# MA  02110-1301, USA.  A copy of the GNU General Public License is
# also available at http://www.gnu.org/copyleft/gpl.html.
from ovirt.node import base, plugins, ui
from ovirt.node.utils import process, system
from subprocess import CalledProcessError
import urllib
import threading
import time

"""
Docker Status
"""


class Plugin(plugins.NodePlugin):
    _model = None
    watcher = None

    def __init__(self, app):
        super(Plugin, self).__init__(app)
        self._model = {}
        self.watcher = DockerWatcher(self)
        self.watcher.start()

    def has_ui(self):
        return True

    def name(self):
        return "Docker"

    def rank(self):
        return 15

    def model(self):
        d = Docker()
        is_alive = d.is_alive()

        model = {"docker.is_alive": "%s" % is_alive,
                 "docker.status": "",
                 "docker.info": "",
                 }

        return model

    def validators(self):
        return {}

    def ui_content(self):
        is_alive = Docker().is_alive()

        DockerAsyncUpdate(self).start()

        ws = [ui.Header("header[0]", "Docker"),
              ui.KeywordLabel("docker.is_alive", "Is Alive: "),
              ui.Divider("divider[0]"),
              ui.KeywordLabel("docker.status", "Status:"),
              ]

        page = ui.Page("page", ws)
        page.buttons = [ui.Button("action.images", "Images",
                                  enabled=is_alive),
                        ui.Button("action.containers", "Containers",
                                  enabled=is_alive)]
        self.widgets.add(page)
        self.widgets.add(page.buttons)
        return page

    def on_change(self, changes):
        pass

    def on_merge(self, changes):
        actions = {"action.images": ["images"],
                   "action.containers": ["ps"],
                   }
        for key in changes:
            if key in actions:
                self._dialog = DockerTxtDialog(actions[key])
                return self._dialog


class DockerTxtDialog(ui.InfoDialog):
    """A simple class to display results of docker subcomands in a dialog
    """
    def __init__(self, subcmd):
        cmd, txt = Docker().docker(subcmd, with_cmd=True)
        title = "$ " + " ".join(cmd)
        super(DockerTxtDialog, self).__init__("dialog.docker.txt", title, txt)


class DockerWatcher(threading.Thread):
    """A thread which watches docker for status changes. If the status changes it updtes the UI
    """
    daemon = True

    def __init__(self, plugin):
        self.plugin = plugin
        self.app = plugin.application
        super(DockerWatcher, self).__init__()

    def run(self):
        try:
            self._run()
        except Exception as e:
            self.app.logger.debug("DockerWatcher", exc_info=True)

    def on_state_change(self):
        DockerAsyncUpdate(self.plugin).run()

    def _run(self):
        d = Docker()
        last_state = None
        while True:
            self.app.logger.debug("Checking docker livelyness")
            time.sleep(1)
            alive = d.is_alive()
            has_changed = last_state != alive
            if has_changed:
                last_state = alive
                self.on_state_change()


class DockerAsyncUpdate(threading.Thread):
    """A thread which gathers information from long running process calls
    In a thread to keep the UI responsive
    """
    daemon = True

    def __init__(self, plugin):
        self.plugin = plugin
        self.app = plugin.application
        super(DockerAsyncUpdate, self).__init__()

    def run(self):
        try:
            self._run()
        except Exception as e:
            self.app.logger.debug("DockerStatusThread", exc_info=True)

    def _run(self):
        d = Docker()
        alive = d.is_alive()
        self._update_ui("docker.is_alive", "%s" % alive)
        self._update_ui("docker.status", d.status())
        #self._update_ui("docker.info", d.info() if alive else "")
        for n, w in self.plugin.widgets.items():
            self.app.logger.debug("%s" % n)
            if n.startswith("action."):
                w.enabled(alive) 

    def _update_ui(self, path, txt):
        con = self.app.ui.thread_connection()
        def update_ui(path=path, txt=txt):
            self.plugin.widgets[path].value(txt)
        con.call(lambda: update_ui())


class Docker(base.Base):
    """A wrapper around several docker related binaries
    """
    port = 4243

    def docker(self, args=[], with_cmd=False):
        """Wrap docker binary
        """
        assert type(args) is list
        cmd = ["docker", "-H", ":%s" % self.port] + args
        ret = process.check_output(cmd, stderr=process.PIPE)
        if with_cmd:
            ret = (cmd, ret)
        return ret

    def service(self, cmd):
        """Wrap docker service
        """
        return system.service("docker", cmd)

    def logs(self):
        return system.journal("docker")

    def status(self):
        status = ""
        try:
            status = self.service("status")
        except process.CalledProcessError as e:
            status = e.output
        return status

    def info(self):
        return self.docker(["info"])

    def is_alive(self):
        alive = False
        try:
            urllib.urlopen('http://127.0.0.1:%s/' % self.port)
            alive = True
        except:
            #self.logger.debug("Docker is  alive")
            pass
        return alive
