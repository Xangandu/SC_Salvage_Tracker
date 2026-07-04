from PySide6.QtCore import Qt

from PySide6.QtGui import QColor, QPalette

from PySide6.QtWidgets import (

    QHeaderView,

    QSizePolicy,

    QTableWidget,

)

from ui.theme_manager import ThemeManager





def configure_mobiglas_table(

    table,

    object_name="dataTable",

    *,

    selectable=True,

):

    table.setObjectName(object_name)

    table.setAlternatingRowColors(True)

    table.setShowGrid(True)

    if selectable:
        table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        table.setSelectionMode(
            QTableWidget.SelectionMode.SingleSelection
        )
    else:
        table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectItems
        )
        table.setSelectionMode(
            QTableWidget.SelectionMode.NoSelection
        )
        table.setFocusPolicy(Qt.FocusPolicy.NoFocus)

    table.verticalHeader().setVisible(False)

    table.setWordWrap(False)



    header = table.horizontalHeader()

    header.setStretchLastSection(False)

    header.setDefaultAlignment(

        Qt.AlignLeft | Qt.AlignVCenter

    )

    header.setHighlightSections(False)

    header.setSectionsClickable(False)



    table.setEditTriggers(

        QTableWidget.NoEditTriggers

    )



    _apply_table_palette(table)

    ThemeManager.apply_table_row_height(table)





def configure_editable_table(

    table,

    object_name="editableTable",

):

    configure_mobiglas_table(

        table,

        object_name,

    )

    table.setEditTriggers(

        QTableWidget.DoubleClicked

        | QTableWidget.EditKeyPressed

        | QTableWidget.SelectedClicked

    )





def finalize_table_columns(

    table,

    stretch_column=-1,

):

    """

    Header und Zellen nach Datenbefüllung synchronisieren.



    Verhindert versetzte Gitterlinien zwischen Kopfzeile

    und Tabelleninhalt (Qt/Stylesheet-Artefakt).

    """

    column_count = table.columnCount()



    if column_count == 0:

        return



    header = table.horizontalHeader()

    header.setStretchLastSection(False)



    if stretch_column is None:

        for col in range(column_count):

            header.setSectionResizeMode(

                col,

                QHeaderView.ResizeMode.ResizeToContents,

            )



        table.resizeColumnsToContents()



        for col in range(column_count):

            width = max(

                header.sectionSize(col),

                header.minimumSectionSize(),

            )

            header.setSectionResizeMode(

                col,

                QHeaderView.ResizeMode.Fixed,

            )

            header.resizeSection(col, width)



        return



    if stretch_column < 0:

        stretch_column = column_count - 1



    for col in range(column_count):

        if col == stretch_column:

            continue



        header.setSectionResizeMode(

            col,

            QHeaderView.ResizeMode.ResizeToContents,

        )



    table.resizeColumnsToContents()



    for col in range(column_count):

        if col == stretch_column:

            header.setSectionResizeMode(

                col,

                QHeaderView.ResizeMode.Stretch,

            )

        else:

            width = max(

                header.sectionSize(col),

                header.minimumSectionSize(),

            )

            header.setSectionResizeMode(

                col,

                QHeaderView.ResizeMode.Fixed,

            )

            header.resizeSection(col, width)





def adjust_table_list_height(

    table,

    *,

    min_rows: int = 2,

    max_visible_rows: int = 8,

) -> None:

    """Höhe an Zeilenanzahl anpassen; ab max_visible_rows intern scrollen."""

    vheader = table.verticalHeader()

    hheader = table.horizontalHeader()

    row_h = vheader.defaultSectionSize()

    header_h = hheader.height() if hheader.isVisible() else 0

    row_count = table.rowCount()

    visible_rows = max(

        min_rows,

        min(row_count if row_count > 0 else min_rows, max_visible_rows),

    )

    frame = table.frameWidth() * 2

    height = header_h + row_h * visible_rows + frame



    table.setMinimumHeight(height)



    if row_count > max_visible_rows:

        capped = header_h + row_h * max_visible_rows + frame

        table.setMaximumHeight(capped)

        table.setVerticalScrollBarPolicy(

            Qt.ScrollBarPolicy.ScrollBarAsNeeded,

        )

    else:

        table.setMaximumHeight(16777215)

        table.setVerticalScrollBarPolicy(

            Qt.ScrollBarPolicy.ScrollBarAlwaysOff,

        )





def finalize_system_list_table(

    table,

    stretch_column: int,

    *,

    max_visible_rows: int = 8,

) -> None:

    """System-Listen: Spalten sinnvoll verteilen, Höhe begrenzen."""

    finalize_table_columns(table, stretch_column=stretch_column)

    adjust_table_list_height(

        table,

        max_visible_rows=max_visible_rows,

    )

    table.setSizePolicy(

        QSizePolicy.Policy.Expanding,

        QSizePolicy.Policy.Fixed,

    )





def _apply_table_palette(table):

    palette = table.palette()

    palette.setColor(
        QPalette.ColorRole.Base,
        QColor(ThemeManager.get_color("table_base")),
    )

    palette.setColor(
        QPalette.ColorRole.AlternateBase,
        QColor(ThemeManager.get_color("table_alternate")),
    )

    palette.setColor(
        QPalette.ColorRole.Text,
        QColor(ThemeManager.get_color("text")),
    )

    palette.setColor(
        QPalette.ColorRole.Highlight,
        QColor(ThemeManager.get_color("table_highlight")),
    )

    palette.setColor(
        QPalette.ColorRole.HighlightedText,
        QColor("#FFFFFF"),
    )

    table.setPalette(palette)

    header = table.horizontalHeader()
    header_palette = header.palette()

    header_color = ThemeManager.get_color("table_header")

    header_palette.setColor(
        QPalette.ColorRole.Window,
        QColor(header_color),
    )

    header_palette.setColor(
        QPalette.ColorRole.Button,
        QColor(header_color),
    )

    header_palette.setColor(
        QPalette.ColorRole.Base,
        QColor(header_color),
    )

    header.setPalette(header_palette)
    header.setAutoFillBackground(True)

    table.setCornerButtonEnabled(False)
    table.viewport().setAutoFillBackground(True)


