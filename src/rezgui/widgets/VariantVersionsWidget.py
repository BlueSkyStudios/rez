from rezgui.qt import QtCore, QtGui
from rezgui.util import create_pane, create_toolbutton
from rezgui.widgets.VariantVersionsTable import VariantVersionsTable
from rezgui.widgets.PackageLoadingWidget import PackageLoadingWidget
from rezgui.mixins.ContextViewMixin import ContextViewMixin
from rez.util import positional_number_string


class VariantVersionsWidget(PackageLoadingWidget, ContextViewMixin):

    closeWindow = QtCore.Signal()

    def __init__(self, context_model=None, reference_variant=None,
                 in_window=False, parent=None):
        """
        Args:
            reference_variant (`Variant`): Used to show the difference between
                two variants.
            in_window (bool): If True, the 'view changelogs' option turns
                into a checkbox, dropping the 'View in window' option.
        """
        super(VariantVersionsWidget, self).__init__(parent)
        ContextViewMixin.__init__(self, context_model)

        self.in_window = in_window
        self.variant = None

        self.label = QtGui.QLabel()
        self.table = VariantVersionsTable(self.context_model,
                                          reference_variant=reference_variant)
        buttons = [None]

        if self.in_window:
            self.changelog_btn = QtGui.QCheckBox("view changelogs")
            self.changelog_btn.stateChanged.connect(self._changelogStateChanged)
            self.changelog_btn.setCheckState(QtCore.Qt.Checked)
            close_btn = QtGui.QPushButton("Close")
            buttons.append(self.changelog_btn)
            buttons.append(close_btn)
            close_btn.clicked.connect(self._close_window)
        else:
            browse_versions_btn = QtGui.QPushButton("Browse Other Versions...")
            browse_versions_btn.clicked.connect(self._browseOtherVersions)
            buttons.append(browse_versions_btn)

            self.changelog_btn, _ = create_toolbutton(
                [("View Changelogs", self._view_or_hide_changelogs),
                 ("View In Window...", self._view_changelogs_window)],
                self)
            buttons.append(self.changelog_btn)

        btn_pane = create_pane(buttons, True, compact=not self.in_window)
        main_widget = create_pane([self.label, self.table, btn_pane], False,
                                  compact=True)

        self.set_main_widget(main_widget)
        self.set_loader_swap_delay(300)
        self.clear()

    def clear(self):
        self.label.setText("no package selected")
        self.table.clear()
        self.setEnabled(False)

    def refresh(self):
        variant = self.variant
        self.variant = None
        self.set_variant(variant)

    def set_variant(self, variant):
        self.stop_loading_packages()

        self.variant = variant
        if self.variant is None:
            self.clear()
            return

        package_paths = self.context_model.packages_path
        if self.variant.search_path not in package_paths:
            self.clear()
            txt = "not on the package search path"
            self.label.setText(txt)
            return

        self.setEnabled(True)
        self.load_packages(package_paths=package_paths,
                           package_name=variant.name,
                           package_attributes=("timestamp",))

    def set_packages(self, packages):
        self.table._set_variant(self.variant, packages)

        self.setEnabled(True)
        diff_num = self.table.get_reference_difference()
        if diff_num is None:
            # normal mode
            if self.table.version_index == 0:
                if self.table.num_versions == 1:
                    txt = "the only package"
                else:
                    txt = "the latest package"
            else:
                nth = positional_number_string(self.table.version_index + 1)
                txt = "the %s latest package" % nth
            if self.table.num_versions > 1:
                txt += " of %d packages" % self.table.num_versions
            txt = "%s is %s" % (self.variant.qualified_package_name, txt)
        else:
            # reference mode - showing difference between two versions
            adj = "ahead" if diff_num > 0 else "behind"
            diff_num = abs(diff_num)
            unit = "version" if diff_num == 1 else "versions"
            txt = "Package is %d %s %s" % (diff_num, unit, adj)

        self.label.setText(txt)

    def _view_changelogs(self, enable):
        label = "Hide Changelogs" if enable else "View Changelogs"
        self.table.set_view_changelog(enable)
        self.changelog_btn.setText(label)
        if isinstance(self.changelog_btn, QtGui.QToolButton):
            self.changelog_btn.defaultAction().setText(label)

    def _changelogStateChanged(self, state):
        self._view_changelogs(state == QtCore.Qt.Checked)
        self.refresh()

    def _view_or_hide_changelogs(self):
        enable = (not self.table.view_changelog)
        self._view_changelogs(enable)
        self.refresh()

    def _view_changelogs_window(self):
        from rezgui.dialogs.VariantVersionsDialog import VariantVersionsDialog
        dlg = VariantVersionsDialog(self.context_model, self.variant,
                                    parent=self)
        dlg.exec_()

    def _browseOtherVersions(self):
        from rezgui.dialogs.BrowsePackageDialog import BrowsePackageDialog
        dlg = BrowsePackageDialog(context_model=self.context_model,
                                  package_text=self.variant.qualified_package_name,
                                  close_only=True,
                                  lock_package=True,
                                  parent=self.parentWidget())

        dlg.setWindowTitle("Versions - %s" % self.variant.name)
        dlg.exec_()

    def _close_window(self):
        self.closeWindow.emit()
