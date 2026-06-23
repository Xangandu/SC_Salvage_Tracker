from PySide6.QtCore import Qt

from PySide6.QtGui import QColor, QPalette

from PySide6.QtWidgets import (

    QHeaderView,

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



    if stretch_column < 0:

        stretch_column = column_count - 1



    header = table.horizontalHeader()

    header.setStretchLastSection(False)



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


