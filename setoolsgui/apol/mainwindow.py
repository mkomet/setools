# Copyright 2015-2016, Tresys Technology, LLC
#
# This file is part of SETools.
#
# SETools is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as
# published by the Free Software Foundation, either version 2.1 of
# the License, or (at your option) any later version.
#
# SETools is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with SETools.  If not, see
# <http://www.gnu.org/licenses/>.
#

import logging

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QFileDialog, QLineEdit, QMainWindow, QMessageBox
from setools import PermissionMap, SELinuxPolicy

from ..widget import SEToolsWidget
from ..logtosignal import LogHandlerToSignal
from .chooseanalysis import ChooseAnalysis
from .summary import SummaryTab


class ApolMainWindow(SEToolsWidget, QMainWindow):

    def __init__(self, filename):
        super(ApolMainWindow, self).__init__()
        self.log = logging.getLogger(__name__)
        self._permmap = None
        self._policy = None
        self.setupUi()

        self.load_permmap()

        if filename:
            self.load_policy(filename)

        if self._policy:
            self.create_new_analysis("Summary", SummaryTab)

        self.update_window_title()

    def setupUi(self):
        self.load_ui("apol.ui")

        self.tab_counter = 0

        # set up analysis menu
        self.chooser = ChooseAnalysis(self)

        # set up error message dialog
        self.error_msg = QMessageBox(self)
        self.error_msg.setStandardButtons(QMessageBox.Ok)

        # set up tab name editor
        self.tab_editor = QLineEdit(self.AnalysisTabs)
        self.tab_editor.setWindowFlags(Qt.Popup)

        # configure tab bar context menu
        tabBar = self.AnalysisTabs.tabBar()
        tabBar.addAction(self.rename_tab_action)
        tabBar.addAction(self.close_tab_action)
        tabBar.setContextMenuPolicy(Qt.ActionsContextMenu)

        # capture INFO and higher Python messages from setools lib for status bar
        handler = LogHandlerToSignal()
        handler.message.connect(self.statusbar.showMessage)
        logging.getLogger("setools").addHandler(handler)
        logging.getLogger("setoolsgui").addHandler(handler)

        # connect signals
        self.open_policy.triggered.connect(self.select_policy)
        self.close_policy_action.triggered.connect(self.close_policy)
        self.open_permmap.triggered.connect(self.select_permmap)
        self.new_analysis.triggered.connect(self.choose_analysis)
        self.AnalysisTabs.tabCloseRequested.connect(self.close_tab)
        self.AnalysisTabs.tabBarDoubleClicked.connect(self.tab_name_editor)
        self.tab_editor.editingFinished.connect(self.rename_tab)
        self.rename_tab_action.triggered.connect(self.rename_active_tab)
        self.close_tab_action.triggered.connect(self.close_active_tab)
        self.copy_action.triggered.connect(self.copy)
        self.cut_action.triggered.connect(self.cut)
        self.paste_action.triggered.connect(self.paste)

        self.show()

    def update_window_title(self):
        if self._policy:
            self.setWindowTitle("{0} - apol".format(self._policy))
        else:
            self.setWindowTitle("apol")

    def select_policy(self):
        old_policy = self._policy

        if old_policy and self.AnalysisTabs.count() > 0:
            reply = QMessageBox.question(
                self, "Continue?",
                "Loading a policy will close all existing analyses.  Continue?",
                QMessageBox.Yes | QMessageBox.No)

            if reply == QMessageBox.No:
                return

        filename = QFileDialog.getOpenFileName(self, "Open policy file", ".")[0]
        if filename:
            self.load_policy(filename)

        if self._policy != old_policy:
            # policy loading succeeded, clear any
            # existing tabs
            self.AnalysisTabs.clear()
            self.create_new_analysis("Summary", SummaryTab)

    def load_policy(self, filename):
        try:
            self._policy = SELinuxPolicy(filename)
        except Exception as ex:
            self.log.critical("Failed to load policy \"{0}\"".format(filename))
            self.error_msg.critical(self, "Policy loading error", str(ex))
        else:
            self.update_window_title()

            if self._permmap:
                self._permmap.map_policy(self._policy)

    def close_policy(self):
        if self.AnalysisTabs.count() > 0:
            reply = QMessageBox.question(
                self, "Continue?",
                "Loading a policy will close all existing analyses.  Continue?",
                QMessageBox.Yes | QMessageBox.No)

            if reply == QMessageBox.No:
                return

        self.AnalysisTabs.clear()
        self._policy = None
        self.update_window_title()

    def select_permmap(self):
        filename = QFileDialog.getOpenFileName(self, "Open permission map file", ".")[0]
        if filename:
            self.load_permmap(filename)

    def load_permmap(self, filename=None):
        try:
            self._permmap = PermissionMap(filename)
        except Exception as ex:
            self.log.critical("Failed to load default permission map: {0}".format(ex))
            self.error_msg.critical(self, "Permission map loading error", str(ex))
        else:
            if self._policy:
                self._permmap.map_policy(self._policy)

    def choose_analysis(self):
        if not self._policy:
            self.error_msg.critical(self, "No open policy",
                                    "Cannot start a new analysis. Please open a policy first.")

            self.select_policy()

        if self._policy:
            # this check of self._policy is here in case someone
            # tries to start an analysis with no policy open, but then
            # cancels out of the policy file chooser or there is an
            # error opening the policy file.
            self.chooser.show(self._policy.mls)

    def create_new_analysis(self, tabtitle, tabclass):
        self.tab_counter += 1
        counted_name = "{0}: {1}".format(self.tab_counter, tabtitle)

        newanalysis = tabclass(self, self._policy, self._permmap)
        newanalysis.setAttribute(Qt.WA_DeleteOnClose)
        newanalysis.setObjectName(counted_name)

        index = self.AnalysisTabs.addTab(newanalysis, counted_name)
        self.AnalysisTabs.setTabToolTip(index, tabtitle)
        self.AnalysisTabs.setCurrentIndex(index)

    def tab_name_editor(self, index):
        if index >= 0:
            tab_area = self.AnalysisTabs.tabBar().tabRect(index)
            self.tab_editor.move(self.AnalysisTabs.mapToGlobal(tab_area.topLeft()))
            self.tab_editor.setText(self.AnalysisTabs.tabText(index))
            self.tab_editor.selectAll()
            self.tab_editor.show()
            self.tab_editor.setFocus()

    def close_active_tab(self):
        """Close the active tab. This is called from the context menu."""
        index = self.AnalysisTabs.currentIndex()
        if index >= 0:
            self.close_tab(index)

    def rename_active_tab(self):
        """Rename the active tab."""
        index = self.AnalysisTabs.currentIndex()
        if index >= 0:
            self.tab_name_editor(index)

    def close_tab(self, index):
        """Close a tab specified by index."""
        widget = self.AnalysisTabs.widget(index)
        widget.close()
        self.AnalysisTabs.removeTab(index)

    def rename_tab(self):
        # this should never be negative since the editor is modal
        index = self.AnalysisTabs.currentIndex()

        self.tab_editor.hide()
        self.AnalysisTabs.setTabText(index, self.tab_editor.text())

    def copy(self):
        """Copy text from the currently-focused widget."""
        try:
            QApplication.instance().focusWidget().copy()
        except AttributeError:
            pass

    def cut(self):
        """Cut text from the currently-focused widget."""
        try:
            QApplication.instance().focusWidget().cut()
        except AttributeError:
            pass

    def paste(self):
        """Paste text into the currently-focused widget."""
        try:
            QApplication.instance().focusWidget().paste()
        except AttributeError:
            pass
