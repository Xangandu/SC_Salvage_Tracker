"""Schrift-Einstellungen — zentrale Kategorien mit Live-Vorschau (MobiGlas-Layout)."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from config.font_families import FONT_FAMILY_LABELS
from config.i18n import tr
from config.typography import (
    INHERIT_FAMILY,
    TYPOGRAPHY_CATEGORIES,
    TYPOGRAPHY_CATEGORY_BY_ID,
    category_default_style,
    resolve_typography_for_ui,
    serialize_typography_settings,
)
from ui.mobiglas_color_dialog import MobiglasColorDialog
from ui.page_layout import form_label, hud_divider
from ui.theme_manager import ThemeManager

_CONTROL_MIN_HEIGHT = 40


def _secondary_button(text: str) -> QPushButton:
    button = QPushButton(text)
    button.setObjectName("secondaryAction")
    button.setAutoDefault(False)
    button.setDefault(False)
    return button


def _style_color_swatch(swatch: QPushButton, color_text: str, fallback: str) -> None:
    color = QColor(color_text)
    if not color.isValid():
        color = QColor(fallback)
    swatch.setStyleSheet(
        f"background-color: {color.name()};"
        "border: 1px solid #33485C;"
        "border-radius: 8px;"
        "padding: 0;"
        "min-width: 40px;"
        "max-width: 40px;"
        "min-height: 40px;"
        "max-height: 40px;"
    )


def _prepare_control(widget) -> None:
    if hasattr(widget, "setMinimumHeight"):
        widget.setMinimumHeight(_CONTROL_MIN_HEIGHT)


def _create_preview_widget(category_id: str, preview_text: str):
    if category_id == "button":
        widget = QPushButton(preview_text)
        widget.setEnabled(False)
        widget.setMinimumHeight(_CONTROL_MIN_HEIGHT)
        return widget
    if category_id == "input":
        widget = QLineEdit(preview_text)
        widget.setReadOnly(True)
        widget.setMinimumHeight(_CONTROL_MIN_HEIGHT)
        return widget
    label = QLabel(preview_text)
    label.setObjectName(
        TYPOGRAPHY_CATEGORY_BY_ID[category_id].preview_object_name
    )
    label.setWordWrap(True)
    label.setMinimumHeight(36)
    return label


class TypographyCategoryRow(QFrame):
    changed = Signal()

    def __init__(
        self,
        category_id: str,
        *,
        global_family_id: str,
        parent=None,
    ):
        super().__init__(parent)
        self.category_id = category_id
        self.category = TYPOGRAPHY_CATEGORY_BY_ID[category_id]
        self._global_family_id = global_family_id
        self._baseline_style = category_default_style(
            self.category,
            family_id=global_family_id,
        )
        self.setObjectName("typographyRoleRow")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(10)

        header = QHBoxLayout()
        title_col = QVBoxLayout()
        title_col.setSpacing(4)
        title_col.addWidget(form_label(tr(self.category.label_key)))
        description = QLabel(tr(self.category.description_key))
        description.setObjectName("mutedLabel")
        description.setWordWrap(True)
        title_col.addWidget(description)
        header.addLayout(title_col, 1)
        reset_button = _secondary_button("↺")
        reset_button.setFixedWidth(40)
        reset_button.setToolTip(tr("typography.reset_role"))
        reset_button.clicked.connect(self.reset_to_default)
        header.addWidget(reset_button)
        layout.addLayout(header)
        layout.addLayout(hud_divider())

        self.family_combo = QComboBox()
        self.family_combo.addItem(
            tr("typography.family.inherit"),
            INHERIT_FAMILY,
        )
        for key, label in FONT_FAMILY_LABELS.items():
            self.family_combo.addItem(label, key)

        self.size_spin = QSpinBox()
        self.size_spin.setRange(8, 72)

        self.weight_combo = QComboBox()
        self.weight_combo.addItem(tr("typography.weight.normal"), 400)
        self.weight_combo.addItem(tr("typography.weight.semibold"), 600)
        self.weight_combo.addItem(tr("typography.weight.bold"), 700)

        self.spacing_spin = QDoubleSpinBox()
        self.spacing_spin.setRange(0.0, 12.0)
        self.spacing_spin.setSingleStep(0.5)
        self.spacing_spin.setDecimals(1)

        self.italic_check = QCheckBox(tr("typography.italic"))

        self.color_input = QLineEdit()
        self.color_input.setPlaceholderText("#RRGGBB")
        self.color_swatch = QPushButton()
        self.color_swatch.setObjectName("designColorSwatch")
        self.color_swatch.setFixedSize(40, 40)
        self.color_swatch.setCursor(Qt.CursorShape.PointingHandCursor)
        self.color_swatch.setAutoDefault(False)
        self.color_swatch.setDefault(False)
        pick_color = _secondary_button(tr("common.choose"))
        pick_color.setFixedWidth(92)
        pick_color.clicked.connect(self._pick_color)
        self.color_swatch.setToolTip(tr("admin.design.color.pick_tooltip"))
        self.color_swatch.clicked.connect(self._pick_color)
        clear_color = _secondary_button("↺")
        clear_color.setFixedWidth(40)
        clear_color.setToolTip(tr("admin.design.color.reset_tooltip"))
        clear_color.clicked.connect(self._reset_color)

        color_row = QHBoxLayout()
        color_row.setSpacing(8)
        color_row.addWidget(self.color_swatch)
        color_row.addWidget(self.color_input, 1)
        color_row.addWidget(pick_color)
        color_row.addWidget(clear_color)

        grid = QGridLayout()
        grid.setHorizontalSpacing(20)
        grid.setVerticalSpacing(14)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)

        field_specs = (
            (tr("typography.field.family"), self.family_combo),
            (tr("typography.field.size"), self.size_spin),
            (tr("typography.field.weight"), self.weight_combo),
            (tr("typography.field.letter_spacing"), self.spacing_spin),
        )
        for index, (label_text, widget) in enumerate(field_specs):
            _prepare_control(widget)
            row = index // 2
            col = index % 2
            cell = QVBoxLayout()
            cell.setSpacing(6)
            cell.addWidget(form_label(label_text))
            cell.addWidget(widget)
            grid.addLayout(cell, row, col)

        color_cell = QVBoxLayout()
        color_cell.setSpacing(6)
        color_cell.addWidget(form_label(tr("typography.field.color")))
        color_host = QWidget()
        color_host.setLayout(color_row)
        color_cell.addWidget(color_host)
        grid.addLayout(color_cell, 2, 0, 1, 2)
        grid.addWidget(self.italic_check, 3, 0, 1, 2)
        layout.addLayout(grid)

        preview_title = form_label(tr("typography.preview_label"))
        layout.addWidget(preview_title)

        preview_box = QFrame()
        preview_box.setObjectName("typographyPreviewBox")
        preview_layout = QVBoxLayout(preview_box)
        preview_layout.setContentsMargins(12, 10, 12, 10)
        self.preview_widget = _create_preview_widget(
            self.category_id,
            tr(self.category.preview_key),
        )
        preview_layout.addWidget(self.preview_widget)
        layout.addWidget(preview_box)

        self.family_combo.currentIndexChanged.connect(self._emit_changed)
        self.size_spin.valueChanged.connect(self._emit_changed)
        self.weight_combo.currentIndexChanged.connect(self._emit_changed)
        self.spacing_spin.valueChanged.connect(self._emit_changed)
        self.color_input.textChanged.connect(self._on_color_changed)
        self.italic_check.toggled.connect(self._emit_changed)

        self.reset_to_default()

    def _emit_changed(self, *_args) -> None:
        self._refresh_preview()
        self.changed.emit()

    def _on_color_changed(self, _text: str) -> None:
        self._refresh_color_swatch()
        self._emit_changed()

    def set_global_family_id(self, family_id: str) -> None:
        self._global_family_id = family_id
        self._refresh_preview()

    def _pick_color(self) -> None:
        current_text = self.color_input.text().strip()
        initial = (
            QColor(current_text)
            if current_text.startswith("#")
            else QColor(self.category.default_color)
        )
        if not initial.isValid():
            initial = QColor(self.category.default_color)
        picked, accepted = MobiglasColorDialog.get_color(
            self,
            tr("typography.color_dialog_title"),
            initial=initial,
        )
        if accepted and picked.isValid():
            self.color_input.setText(picked.name().upper())

    def _reset_color(self) -> None:
        baseline_color = str(
            self._baseline_style.get("color", self.category.default_color)
        ).upper()
        self.color_input.setText(baseline_color)

    def _refresh_color_swatch(self) -> None:
        _style_color_swatch(
            self.color_swatch,
            self.color_input.text().strip(),
            self.category.default_color,
        )

    def set_baseline_style(self, style: dict) -> None:
        self._baseline_style = dict(style)

    def reset_to_default(self) -> None:
        self.set_style(self._baseline_style, block_signals=True)

    def set_style(self, style: dict, *, block_signals: bool = False) -> None:
        if block_signals:
            self.family_combo.blockSignals(True)
            self.size_spin.blockSignals(True)
            self.weight_combo.blockSignals(True)
            self.spacing_spin.blockSignals(True)
            self.color_input.blockSignals(True)
            self.italic_check.blockSignals(True)

        family_index = self.family_combo.findData(
            style.get("family_id", INHERIT_FAMILY)
        )
        if family_index < 0:
            family_index = 0
        self.family_combo.setCurrentIndex(family_index)
        self.size_spin.setValue(
            int(style.get("size_px", self.category.default_size_px))
        )
        weight = int(style.get("weight", self.category.default_weight))
        weight_index = self.weight_combo.findData(weight)
        if weight_index < 0:
            weight_index = 0
        self.weight_combo.setCurrentIndex(weight_index)
        self.spacing_spin.setValue(
            float(
                style.get(
                    "letter_spacing_px",
                    self.category.default_letter_spacing_px,
                )
                or 0
            )
        )
        self.color_input.setText(
            str(style.get("color", self.category.default_color)).upper()
        )
        self.italic_check.setChecked(
            bool(style.get("italic", self.category.italic))
        )

        if block_signals:
            self.family_combo.blockSignals(False)
            self.size_spin.blockSignals(False)
            self.weight_combo.blockSignals(False)
            self.spacing_spin.blockSignals(False)
            self.color_input.blockSignals(False)
            self.italic_check.blockSignals(False)

        self._refresh_color_swatch()
        self._refresh_preview()

    def collect_style(self) -> dict:
        return {
            "family_id": self.family_combo.currentData() or INHERIT_FAMILY,
            "size_px": self.size_spin.value(),
            "weight": int(self.weight_combo.currentData() or 400),
            "letter_spacing_px": float(self.spacing_spin.value()),
            "color": self.color_input.text().strip().upper(),
            "italic": self.italic_check.isChecked(),
        }

    def _refresh_preview(self) -> None:
        stylesheet = ThemeManager.build_typography_preview_stylesheet(
            self.category_id,
            self.collect_style(),
            global_family_id=self._global_family_id,
        )
        if stylesheet:
            self.preview_widget.setStyleSheet(stylesheet)


class TypographySettingsPanel(QWidget):
    changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("typographySettingsPanel")
        self._global_family_id = ThemeManager.current_settings().get(
            "font_family",
            "oxanium",
        )
        self._theme_id = ThemeManager.current_settings().get(
            "theme",
            "star_citizen",
        )
        self._baseline_styles: dict[str, dict] = {}
        self._category_rows: dict[str, TypographyCategoryRow] = {}

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        hint = QLabel(tr("admin.design.hint.typography"))
        hint.setObjectName("mutedLabel")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        toolbar = QHBoxLayout()
        toolbar.setSpacing(12)
        reset_all = _secondary_button(tr("typography.reset_all"))
        reset_all.clicked.connect(self.reset_all_to_defaults)
        toolbar.addWidget(reset_all)
        toolbar.addStretch()
        layout.addLayout(toolbar)

        categories_host = QWidget()
        categories_host.setObjectName("typographyRolesHost")
        categories_layout = QVBoxLayout(categories_host)
        categories_layout.setContentsMargins(0, 0, 0, 0)
        categories_layout.setSpacing(18)

        for category in TYPOGRAPHY_CATEGORIES:
            row = TypographyCategoryRow(
                category.category_id,
                global_family_id=self._global_family_id,
            )
            row.changed.connect(self.changed.emit)
            self._category_rows[category.category_id] = row
            categories_layout.addWidget(row)

        layout.addWidget(categories_host)

    def set_global_family_id(self, family_id: str) -> None:
        self._global_family_id = family_id
        for row in self._category_rows.values():
            row.set_global_family_id(family_id)

    def reset_all_to_defaults(self) -> None:
        for row in self._category_rows.values():
            row.reset_to_default()
        self.changed.emit()

    def load_from_settings(
        self,
        typography_json: str,
        *,
        typography_baseline_json: str = "",
        theme_id: str = "star_citizen",
        global_family_id: str,
    ) -> None:
        self._global_family_id = global_family_id
        self._theme_id = theme_id
        display_styles, self._baseline_styles = resolve_typography_for_ui(
            typography_json,
            typography_baseline_json,
            theme_id=theme_id,
            global_family_id=global_family_id,
        )
        for category_id, row in self._category_rows.items():
            row.set_global_family_id(global_family_id)
            row.set_baseline_style(
                self._baseline_styles.get(
                    category_id,
                    category_default_style(
                        row.category,
                        family_id=global_family_id,
                    ),
                )
            )
            row.set_style(
                display_styles.get(
                    category_id,
                    category_default_style(
                        row.category,
                        family_id=global_family_id,
                    ),
                ),
                block_signals=True,
            )

    def collect_form_styles(self) -> dict[str, dict]:
        return {
            category_id: row.collect_style()
            for category_id, row in self._category_rows.items()
        }

    def collect_overrides_json(self) -> str:
        saved = ThemeManager.normalize_typography_overrides_for_save(
            self.collect_form_styles(),
            global_family_id=self._global_family_id,
        )
        return serialize_typography_settings(saved)
