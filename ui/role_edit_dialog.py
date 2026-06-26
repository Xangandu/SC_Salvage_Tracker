from PySide6.QtCore import QObject, QEvent, Qt, QTimer
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import (
    QApplication,    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QCheckBox,
    QScrollArea,
    QFrame,
    QWidget,
    QMessageBox,
    QSizePolicy,
)

from config.permissions import (
    PERMISSION_GROUPS,
    PERM_DATABASE_RESET,
    ROLE_ADMIN,
    ALL_PERMISSION_NAMES,
)
from config.i18n import (
    permission_group_label,
    permission_label,
    tr,
)
from ui.page_layout import (
    add_form_field,
    primary_button,
    hud_divider,
    subsection_title,
    page_panel,
)
from ui.mobiglas_window_frame import (
    MobiglasFramelessMixin,
    apply_mobiglas_window_frame,
)


def _preferred_dialog_size():
    screen = QGuiApplication.primaryScreen()

    if screen is None:
        return 760, 900

    available = screen.availableGeometry()
    width = min(760, max(680, int(available.width() * 0.52)))
    height = min(920, max(820, int(available.height() * 0.88)))

    return width, height


class _PermissionScrollWheelFilter(QObject):
    """Leitet Mausrad-Events an die Rechte-ScrollArea weiter."""

    def __init__(self, scroll_area):
        super().__init__()
        self._scroll_area = scroll_area

    def eventFilter(self, watched, event):
        if event.type() != QEvent.Type.Wheel:
            return False

        viewport = self._scroll_area.viewport()
        QApplication.sendEvent(viewport, event)
        return True


class RoleEditDialog(MobiglasFramelessMixin, QDialog):
    def __init__(
        self,
        parent=None,
        role=None,
        permissions=None,
        read_only=False,
        grantable_permissions=None,
    ):
        super().__init__(parent)

        self.role = role or {}
        self.read_only = read_only
        self._checkboxes = {}
        self._grantable = set(
            grantable_permissions
            if grantable_permissions is not None
            else ALL_PERMISSION_NAMES
        )

        is_edit = bool(role)
        if read_only:
            title = tr(
                "role.dialog.view",
                name=role.get("role_name", ""),
            )
        elif is_edit:
            title = tr("role.dialog.edit")
        else:
            title = tr("role.dialog.new")

        self.setObjectName("mobiglasDialog")
        self.setWindowTitle(title)
        self.setModal(True)

        width, height = _preferred_dialog_size()
        self.resize(width, height)
        self.setMinimumSize(680, 820)

        layout = QVBoxLayout()
        layout.setSpacing(14)
        layout.setContentsMargins(24, 20, 24, 20)

        header = subsection_title(f"◆ {title.upper()}")
        layout.addWidget(header)
        layout.addLayout(hud_divider())

        panel = QFrame()
        panel.setObjectName("pagePanel")
        form = QVBoxLayout(panel)
        form.setSpacing(10)
        form.setContentsMargins(16, 16, 16, 16)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText(
            tr("role.dialog.placeholder.name")
        )
        if role:
            self.name_input.setText(role.get("role_name", ""))
        add_form_field(form, tr("role.dialog.label.name"), self.name_input)

        self.description_input = QLineEdit()
        self.description_input.setPlaceholderText(
            tr("role.dialog.placeholder.description")
        )
        if role:
            self.description_input.setText(
                role.get("description", "")
            )
        add_form_field(
            form,
            tr("role.dialog.label.description"),
            self.description_input,
        )

        layout.addWidget(panel)

        layout.addWidget(subsection_title(tr("role.dialog.section.permissions")))
        layout.addLayout(hud_divider())

        if not read_only:
            preset_row = QHBoxLayout()
            preset_row.setSpacing(8)

            all_button = QPushButton(tr("role.dialog.select_all"))
            all_button.setObjectName("secondaryAction")
            all_button.clicked.connect(
                lambda: self._set_all_permissions(True)
            )
            preset_row.addWidget(all_button)

            none_button = QPushButton(tr("role.dialog.select_none"))
            none_button.setObjectName("secondaryAction")
            none_button.clicked.connect(
                lambda: self._set_all_permissions(False)
            )
            preset_row.addWidget(none_button)

            except_db_button = QPushButton(
                tr("role.dialog.select_except_db")
            )
            except_db_button.setObjectName("secondaryAction")
            except_db_button.clicked.connect(
                self._select_all_except_database
            )
            preset_row.addWidget(except_db_button)
            preset_row.addStretch()
            layout.addLayout(preset_row)

            scroll_hint = QLabel(tr("role.dialog.scroll_hint"))
            scroll_hint.setObjectName("mutedLabel")
            scroll_hint.setWordWrap(True)
            layout.addWidget(scroll_hint)

            if len(self._grantable) < len(ALL_PERMISSION_NAMES):
                limit_hint = QLabel(tr("role.dialog.limit_hint"))
                limit_hint.setObjectName("mutedLabel")
                limit_hint.setWordWrap(True)
                layout.addWidget(limit_hint)

        perm_panel, perm_panel_layout = page_panel()
        perm_panel_layout.setContentsMargins(16, 16, 16, 16)
        perm_panel_layout.setSpacing(0)
        perm_panel.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )

        self._perm_scroll = QScrollArea()
        self._perm_scroll.setWidgetResizable(True)
        self._perm_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._perm_scroll.setObjectName("rolePermissionsScroll")
        self._perm_scroll.viewport().setObjectName(
            "rolePermissionsViewport"
        )
        self._perm_scroll.setMinimumHeight(320)
        self._perm_scroll.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOn
        )
        self._perm_scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self._perm_scroll.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )

        self._perm_host = QWidget()
        self._perm_host.setObjectName("rolePermissionsContent")
        perm_layout = QHBoxLayout(self._perm_host)
        perm_layout.setContentsMargins(0, 0, 0, 0)
        perm_layout.setSpacing(20)

        assigned = set(permissions or [])
        split_at = (len(PERMISSION_GROUPS) + 1) // 2
        column_groups = (
            PERMISSION_GROUPS[:split_at],
            PERMISSION_GROUPS[split_at:],
        )

        for groups in column_groups:
            column = QWidget()
            column_layout = QVBoxLayout(column)
            column_layout.setContentsMargins(0, 0, 0, 0)
            column_layout.setSpacing(14)

            for group_name, permission_names in groups:
                column_layout.addWidget(
                    self._build_permission_group(
                        group_name,
                        permission_names,
                        assigned,
                    )
                )

            column_layout.addStretch()
            perm_layout.addWidget(column, 1)

        self._perm_scroll.setWidget(self._perm_host)
        perm_panel_layout.addWidget(self._perm_scroll, 1)
        layout.addWidget(perm_panel, stretch=1)

        self._perm_wheel_filter = _PermissionScrollWheelFilter(
            self._perm_scroll
        )
        self._install_permission_wheel_forward(self._perm_host)

        if read_only:
            self.name_input.setReadOnly(True)
            self.description_input.setReadOnly(True)
            for checkbox in self._checkboxes.values():
                checkbox.setEnabled(False)

        buttons = QHBoxLayout()
        buttons.addStretch()

        if read_only:
            close_button = QPushButton(tr("common.close"))
            close_button.setObjectName("secondaryAction")
            close_button.clicked.connect(self.reject)
            buttons.addWidget(close_button)
        else:
            cancel_button = QPushButton(tr("common.cancel"))
            cancel_button.setObjectName("secondaryAction")
            cancel_button.clicked.connect(self.reject)
            buttons.addWidget(cancel_button)

            save_button = primary_button(tr("common.save"))
            save_button.clicked.connect(
                self._validate_and_accept
            )
            buttons.addWidget(save_button)

        layout.addLayout(buttons)
        self.setLayout(layout)

        apply_mobiglas_window_frame(
            self,
            title=title,
            dialog=True,
        )

    def showEvent(self, event):
        super().showEvent(event)
        QTimer.singleShot(0, self._refresh_permission_layout)

    def _refresh_permission_layout(self):
        if not hasattr(self, "_perm_scroll"):
            return

        self._perm_host.adjustSize()
        self._perm_scroll.updateGeometry()

    def _install_permission_wheel_forward(self, root):
        root.installEventFilter(self._perm_wheel_filter)
        for child in root.findChildren(QWidget):
            child.installEventFilter(self._perm_wheel_filter)

    def _build_permission_group(
        self,
        group_name,
        permission_names,
        assigned,
    ):
        group_frame = QFrame()
        group_frame.setObjectName("rolePermissionGroup")

        group_layout = QVBoxLayout(group_frame)
        group_layout.setContentsMargins(12, 10, 12, 12)
        group_layout.setSpacing(8)

        group_label = QLabel(
            f"◆ {permission_group_label(group_name)}"
        )
        group_label.setObjectName("subSectionTitle")
        group_layout.addWidget(group_label)

        for permission_name in permission_names:
            label = permission_label(permission_name)
            checkbox = QCheckBox(label)
            checkbox.setChecked(
                permission_name in assigned
            )
            if not self.read_only:
                if permission_name not in self._grantable:
                    checkbox.setEnabled(False)
                    if permission_name in assigned:
                        checkbox.setToolTip(
                            tr("role.dialog.tooltip.assigned_locked")
                        )
                    else:
                        checkbox.setToolTip(
                            tr("role.dialog.tooltip.not_grantable")
                        )
            self._checkboxes[permission_name] = checkbox
            group_layout.addWidget(checkbox)

        return group_frame

    def _set_all_permissions(self, checked):
        for name, checkbox in self._checkboxes.items():
            if checkbox.isEnabled():
                checkbox.setChecked(checked)

    def _select_all_except_database(self):
        for name, checkbox in self._checkboxes.items():
            if not checkbox.isEnabled():
                continue
            checkbox.setChecked(name != PERM_DATABASE_RESET)

    def _validate_and_accept(self):
        if not self.name_input.text().strip():
            QMessageBox.warning(
                self,
                tr("role.dialog.msg.title"),
                tr("role.dialog.msg.name_required"),
            )
            return

        if (
            self.name_input.text().strip() == ROLE_ADMIN
            and self.role.get("role_name") != ROLE_ADMIN
        ):
            QMessageBox.warning(
                self,
                tr("role.dialog.msg.title"),
                tr("role.dialog.msg.admin_reserved"),
            )
            return

        self.accept()

    def result_data(self):
        return {
            "role_name": self.name_input.text().strip(),
            "description": (
                self.description_input.text().strip()
                or None
            ),
            "permissions": [
                name
                for name, box in self._checkboxes.items()
                if box.isChecked()
            ],
        }
