# Copyright 2016, Tresys Technology, LLC
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

from PyQt5.QtCore import Qt, QSortFilterProxyModel, QStringListModel, QThread
from PyQt5.QtGui import QPalette, QTextCursor
from PyQt5.QtWidgets import QCompleter, QHeaderView, QMessageBox, QProgressDialog, QScrollArea
from setools import MLSRuleQuery

from ..logtosignal import LogHandlerToSignal
from ..models import SEToolsListModel, invert_list_selection
from ..mlsrulemodel import MLSRuleTableModel
from ..widget import SEToolsWidget
from .queryupdater import QueryResultsUpdater


class SummaryTab(SEToolsWidget, QScrollArea):

    """An SELinux policy summary."""

    def __init__(self, parent, policy, perm_map):
        super(SummaryTab, self).__init__(parent)
        self.log = logging.getLogger(__name__)
        self.setupUi(policy)

    def setupUi(self, p):
        self.load_ui("summary.ui")

        # Ensure settings are consistent with the initial .ui state
        self.notes.setHidden(not self.notes_expander.isChecked())

        # Populate policy stats
        mls = "enabled" if p.mls else "disabled"

        self.policy_version.setText(str(p.version))
        self.mls.setText(mls)
        self.handle_unknown.setText(p.handle_unknown)
        self.class_count.setText(str(p.class_count))
        self.perms_count.setText(str(p.permission_count))
        self.sensitivity_count.setText(str(p.level_count))
        self.category_count.setText(str(p.category_count))
        self.type_count.setText(str(p.type_count))
        self.attribute_count.setText(str(p.type_attribute_count))
        self.user_count.setText(str(p.user_count))
        self.role_count.setText(str(p.role_count))
        self.bool_count.setText(str(p.boolean_count))
        self.allow_count.setText(str(p.allow_count))
        self.neverallow_count.setText(str(p.neverallow_count))
        self.auditallow_count.setText(str(p.auditallow_count))
        self.dontaudit_count.setText(str(p.dontaudit_count))
        self.type_transition_count.setText(str(p.type_transition_count))
        self.type_change_count.setText(str(p.type_change_count))
        self.type_member_count.setText(str(p.type_member_count))
        self.range_transition_count.setText(str(p.range_transition_count))
        self.role_allow_count.setText(str(p.role_allow_count))
        self.role_transition_count.setText(str(p.role_transition_count))
        self.constrain_count.setText(str(p.constraint_count))
        self.validatetrans_count.setText(str(p.validatetrans_count))
        self.mlsconstrain_count.setText(str(p.mlsconstraint_count))
        self.mlsvalidatetrans_count.setText(str(p.mlsvalidatetrans_count))
        self.permissive_count.setText(str(p.permissives_count))
        self.default_count.setText(str(p.default_count))
        self.typebounds_count.setText(str(p.typebounds_count))
        self.allowxperm_count.setText(str(p.allowxperm_count))
        self.neverallowxperm_count.setText(str(p.neverallowxperm_count))
        self.auditallowxperm_count.setText(str(p.auditallowxperm_count))
        self.dontauditxperm_count.setText(str(p.dontauditxperm_count))
        self.initsid_count.setText(str(p.initialsids_count))
        self.fs_use_count.setText(str(p.fs_use_count))
        self.genfscon_count.setText(str(p.genfscon_count))
        self.portcon_count.setText(str(p.portcon_count))
        self.netifcon_count.setText(str(p.netifcon_count))
        self.nodecon_count.setText(str(p.nodecon_count))

        # Fill policy capabilities list
        self.polcaps.addItems([str(c) for c in p.polcaps()])
