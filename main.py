"""
main.py

Entry point for the modular building / construction programmer.

Currently implemented:
- Tab 1: Breeze Block Calculator (walls + half-circle arcs).

Architecture
------------
- block_data.py: data definitions for block sizes/prices.
- breeze_block_tab.py: PyQt5 widget for block calculations.
- main.py: creates a tabbed main window and applies a dark theme.

Run
---
python main.py
"""

import sys

from PyQt5 import QtCore, QtGui, QtWidgets

from modules.breeze_block_tab import BreezeBlockTab
from modules.sweet_sand_tab import SweetSandTab
from modules.concrete_tab import ConcreteTab
from modules.land_prep_tab import LandPrepTab
from modules.manpower_tab import ManpowerTab
from modules.equipment_tab import EquipmentTab
from modules.summary_tab import SummaryTab


class MainWindow(QtWidgets.QMainWindow):
    """
    Main application window with a QTabWidget for different tools.

    Adds:
    - File menu: New / Open / Save / Save As
    - Saves and loads a single project JSON file containing ALL tab inputs
    """

    def __init__(self) -> None:
        super().__init__()

        from modules.project_io import PROJECT_FILE_EXT, load_project, save_project

        self._PROJECT_FILE_EXT = PROJECT_FILE_EXT
        self._load_project_file = load_project
        self._save_project_file = save_project

        self._current_project_path: str | None = None

        # Create the QTabWidget
        self.tab_widget = QtWidgets.QTabWidget(self)
        self.setCentralWidget(self.tab_widget)

        # --- Create all functional tabs ---
        self.breeze_tab = BreezeBlockTab(self)
        self.sweet_sand_tab = SweetSandTab(self)
        self.concrete_tab = ConcreteTab(self)
        self.land_prep_tab = LandPrepTab(self)
        self.manpower_tab = ManpowerTab(self)
        self.equipment_tab = EquipmentTab(self)

        # Add them (excluding summary for the moment)
        self.tab_widget.addTab(self.breeze_tab, "Breeze Block Calculator")
        self.tab_widget.addTab(self.sweet_sand_tab, "Sweet Sand Calculator")
        self.tab_widget.addTab(self.concrete_tab, "Concrete Works")
        self.tab_widget.addTab(self.land_prep_tab, "Land Preparation")
        self.tab_widget.addTab(self.manpower_tab, "Manpower")
        self.tab_widget.addTab(self.equipment_tab, "Equipment and Machinery")

        # --- Summary tab as FIRST tab ---
        self.summary_tab = SummaryTab(
            breeze_tab=self.breeze_tab,
            sweet_sand_tab=self.sweet_sand_tab,
            concrete_tab=self.concrete_tab,
            land_prep_tab=self.land_prep_tab,
            manpower_tab=self.manpower_tab,
            equipment_tab=self.equipment_tab,
            parent=self,
        )
        self.tab_widget.insertTab(0, self.summary_tab, "Summary")
        self.tab_widget.setCurrentIndex(0)

        # Ensure the summary refreshes whenever the user switches to it
        self.tab_widget.currentChanged.connect(self._on_tab_changed)

        # Theme / styling
        self._apply_dark_theme()
        self._apply_styles()

        self.setWindowTitle("GDT Construction Planner")
        self.resize(900, 700)

        # File menu actions
        self._build_menus()
        self._update_title()

    # ------------------------------------------------------------------
    # Menus
    # ------------------------------------------------------------------

    def _build_menus(self) -> None:
        menubar = self.menuBar()
        file_menu = menubar.addMenu("&File")

        act_new = QtWidgets.QAction("New Project", self)
        act_new.setShortcut("Ctrl+N")
        act_new.triggered.connect(self._new_project)

        act_open = QtWidgets.QAction("Open Project…", self)
        act_open.setShortcut("Ctrl+O")
        act_open.triggered.connect(self._open_project)

        act_save = QtWidgets.QAction("Save Project", self)
        act_save.setShortcut("Ctrl+S")
        act_save.triggered.connect(self._save_project)

        act_save_as = QtWidgets.QAction("Save Project As…", self)
        act_save_as.setShortcut("Ctrl+Shift+S")
        act_save_as.triggered.connect(self._save_project_as)

        file_menu.addAction(act_new)
        file_menu.addSeparator()
        file_menu.addAction(act_open)
        file_menu.addSeparator()
        file_menu.addAction(act_save)
        file_menu.addAction(act_save_as)

    def _update_title(self) -> None:
        if self._current_project_path:
            self.setWindowTitle(f"GDT Construction Planner  |  {self._current_project_path}")
        else:
            self.setWindowTitle("GDT Construction Planner")




    def _on_tab_changed(self, index: int) -> None:
        """
        When user switches to Summary, force a full recalc first so the totals are correct.
        """
        widget = self.tab_widget.widget(index)
        if widget is self.summary_tab:
            self._recalculate_all_tabs()
            self.summary_tab.refresh_summary()


    # ------------------------------------------------------------------
    # Project state (collect/apply)
    # ------------------------------------------------------------------

    def _collect_project_state(self) -> dict:
        """
        Grab all user-input values from every tab into one dict.
        """
        return {
            "breeze_block": self.breeze_tab.export_state(),
            "sweet_sand": self.sweet_sand_tab.export_state(),
            "concrete": self.concrete_tab.export_state(),
            "land_prep": self.land_prep_tab.export_state(),
            "manpower": self.manpower_tab.export_state(),
            "equipment": self.equipment_tab.export_state(),
        }


    def _apply_project_state(self, state: dict) -> None:
        """
        Push a loaded dict back into the UI, then recalc everything so Summary is correct.
        """
        self.breeze_tab.import_state(state.get("breeze_block", {}))
        self.sweet_sand_tab.import_state(state.get("sweet_sand", {}))
        self.concrete_tab.import_state(state.get("concrete", {}))
        self.land_prep_tab.import_state(state.get("land_prep", {}))
        self.manpower_tab.import_state(state.get("manpower", {}))
        self.equipment_tab.import_state(state.get("equipment", {}))

        # Auto-recompute all derived outputs (so Summary isn't stale)
        self._recalculate_all_tabs()

        # Now refresh summary once everything is “real”
        try:
            self.summary_tab.refresh_summary()
        except Exception:
            pass



    def _recalculate_all_tabs(self) -> None:
        """
        Force every calculator tab to recompute its outputs so Summary is always correct.

        Important:
        - ConcreteTab supports silent recalculation to avoid QMessageBox spam.
        - Other tabs use their existing calculate slot.
        """
        tabs = [
            self.breeze_tab,
            self.sweet_sand_tab,
            self.concrete_tab,
            self.land_prep_tab,
            self.manpower_tab,
            self.equipment_tab,
        ]

        for tab in tabs:
            try:
                # Prefer a public recalc hook if present
                if hasattr(tab, "recalculate"):
                    try:
                        tab.recalculate(show_dialogs=False)  # ConcreteTab accepts this
                    except TypeError:
                        tab.recalculate()  # other tabs might not take args
                    continue

                # Fall back to the existing button handler
                if hasattr(tab, "_on_calculate_clicked"):
                    tab._on_calculate_clicked()

            except Exception:
                # Never crash the whole app because one tab had weird state.
                pass





    # ------------------------------------------------------------------
    # File actions
    # ------------------------------------------------------------------

    def _new_project(self) -> None:
        """
        Reset all tabs to defaults and clear current project path.
        """
        self.breeze_tab._on_reset_clicked()
        self.sweet_sand_tab._on_reset_clicked()
        self.concrete_tab._on_reset_clicked()
        self.land_prep_tab._on_reset_clicked()
        self.manpower_tab._on_reset_clicked()
        self.equipment_tab._on_reset_clicked()

        self._current_project_path = None
        self._update_title()

        try:
            self.summary_tab.refresh_summary()
        except Exception:
            pass

    def _open_project(self) -> None:
        """
        Load a .gdtproj.json and restore the UI.
        """
        filt = f"GDT Project (*{self._PROJECT_FILE_EXT});;JSON (*.json);;All Files (*.*)"
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Open Project",
            "",
            filt,
        )
        if not path:
            return

        try:
            data = self._load_project_file(path)
        except Exception as exc:
            QtWidgets.QMessageBox.critical(
                self,
                "Open Failed",
                f"Could not open project file:\n\n{exc}",
            )
            return

        self._apply_project_state(data)
        self._current_project_path = path
        self._update_title()

    def _save_project(self) -> None:
        """
        Save to current path, or fall back to Save As.
        """
        if not self._current_project_path:
            self._save_project_as()
            return

        try:
            state = self._collect_project_state()
            self._save_project_file(self._current_project_path, state)
        except Exception as exc:
            QtWidgets.QMessageBox.critical(
                self,
                "Save Failed",
                f"Could not save project:\n\n{exc}",
            )
            return

        QtWidgets.QMessageBox.information(self, "Saved", "Project saved successfully.")

    def _save_project_as(self) -> None:
        """
        Save to a new file path.
        """
        filt = f"GDT Project (*{self._PROJECT_FILE_EXT});;JSON (*.json);;All Files (*.*)"
        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self,
            "Save Project As",
            "my_project" + self._PROJECT_FILE_EXT,
            filt,
        )
        if not path:
            return

        # Enforce extension if user deletes it
        if not path.endswith(self._PROJECT_FILE_EXT):
            path += self._PROJECT_FILE_EXT

        try:
            state = self._collect_project_state()
            self._save_project_file(path, state)
        except Exception as exc:
            QtWidgets.QMessageBox.critical(
                self,
                "Save Failed",
                f"Could not save project:\n\n{exc}",
            )
            return

        self._current_project_path = path
        self._update_title()

        QtWidgets.QMessageBox.information(self, "Saved", "Project saved successfully.")



    def _apply_dark_theme(self) -> None:
        """
        Set a dark-blue + orange palette for the whole app.
        Palette handles base widget colours; QSS handles the finer details.
        """
        app = QtWidgets.QApplication.instance()
        if app is None:
            return

        # Signature colours
        BG = QtGui.QColor("#050B1A")          # deep navy
        BG_ALT = QtGui.QColor("#0B1020")      # slightly lighter panels
        BASE = QtGui.QColor("#0E1630")        # input backgrounds
        TEXT = QtGui.QColor("#F5F5F5")        # main text
        TEXT_DIM = QtGui.QColor("#A9B0C5")    # secondary text
        ORANGE = QtGui.QColor("#FF7A00")      # vibrant accent
        DISABLED = QtGui.QColor("#6B7280")

        palette = QtGui.QPalette()

        palette.setColor(QtGui.QPalette.Window, BG)
        palette.setColor(QtGui.QPalette.WindowText, TEXT)

        palette.setColor(QtGui.QPalette.Base, BASE)
        palette.setColor(QtGui.QPalette.AlternateBase, BG_ALT)

        palette.setColor(QtGui.QPalette.Text, TEXT)
        palette.setColor(QtGui.QPalette.Disabled, QtGui.QPalette.Text, DISABLED)

        palette.setColor(QtGui.QPalette.Button, BG_ALT)
        palette.setColor(QtGui.QPalette.ButtonText, TEXT)
        palette.setColor(QtGui.QPalette.Disabled, QtGui.QPalette.ButtonText, DISABLED)

        palette.setColor(QtGui.QPalette.ToolTipBase, BG_ALT)
        palette.setColor(QtGui.QPalette.ToolTipText, TEXT)

        palette.setColor(QtGui.QPalette.Highlight, ORANGE)
        palette.setColor(QtGui.QPalette.HighlightedText, QtGui.QColor("#050B1A"))

        app.setPalette(palette)
        app.setStyle("Fusion")




    def _apply_styles(self) -> None:
        """
        Apply a consistent dark-blue + orange stylesheet across all widgets.
        Uses objectName hooks:
        - QPushButton#primaryButton
        - QPushButton#secondaryButton
        """
        app = QtWidgets.QApplication.instance()
        if app is None:
            return

        ORANGE = "#FF7A00"
        ORANGE_HOVER = "#FF8E2B"
        ORANGE_PRESSED = "#E96F00"

        BG = "#050B1A"
        PANEL = "#0B1020"
        PANEL_2 = "#0E1630"
        BORDER = "#223056"
        TEXT = "#F5F5F5"
        TEXT_DIM = "#A9B0C5"

        app.setStyleSheet(
            f"""
            /* -------------------------
            GLOBAL / BASE
            --------------------------*/
            QWidget {{
                background-color: {BG};
                color: {TEXT};
                font-size: 13px;
            }}

            QMainWindow {{
                background-color: {BG};
            }}

            /* -------------------------
            TABS
            --------------------------*/
            QTabWidget::pane {{
                border-top: 2px solid {ORANGE};
                background: {BG};
            }}

            QTabBar::tab {{
                background: {PANEL};
                color: {TEXT_DIM};
                padding: 7px 16px;
                margin-right: 2px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                border: 1px solid {BORDER};
                border-bottom: none;
            }}

            QTabBar::tab:selected {{
                background: {PANEL_2};
                color: {TEXT};
            }}

            QTabBar::tab:hover {{
                color: {TEXT};
                border: 1px solid {ORANGE};
                border-bottom: none;
            }}

            /* -------------------------
            GROUP BOXES
            --------------------------*/
            QGroupBox {{
                border: 1px solid {BORDER};
                border-radius: 10px;
                margin-top: 18px;
                padding: 12px;
                background-color: {PANEL};
            }}

            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 8px;
                color: {TEXT};
                font-weight: bold;
            }}

            /* -------------------------
            INPUTS
            --------------------------*/
            QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox, QPlainTextEdit, QTextEdit {{
                background-color: {PANEL_2};
                color: {TEXT};
                border: 1px solid {BORDER};
                border-radius: 8px;
                padding: 4px 8px;
                selection-background-color: {ORANGE};
                selection-color: {BG};
            }}

            QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus,
            QPlainTextEdit:focus, QTextEdit:focus {{
                border: 1px solid {ORANGE};
            }}

            QComboBox::drop-down {{
                border: 0px;
                width: 28px;
            }}

            QComboBox QAbstractItemView {{
                background-color: {PANEL};
                color: {TEXT};
                border: 1px solid {BORDER};
                selection-background-color: {ORANGE};
                selection-color: {BG};
            }}

            /* -------------------------
            SCROLLBARS
            --------------------------*/
            QScrollBar:vertical {{
                background: {PANEL};
                width: 12px;
                margin: 0px;
                border-radius: 6px;
            }}
            QScrollBar::handle:vertical {{
                background: {ORANGE};
                min-height: 24px;
                border-radius: 6px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {ORANGE_HOVER};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background: none;
            }}

            /* -------------------------
            BUTTONS
            --------------------------*/
            QPushButton {{
                background-color: {PANEL_2};
                color: {TEXT};
                border: 1px solid {BORDER};
                border-radius: 10px;
                padding: 8px 14px;
            }}

            QPushButton:hover {{
                border: 1px solid {ORANGE};
            }}

            QPushButton#primaryButton {{
                background-color: {ORANGE};
                color: {BG};
                font-weight: bold;
                border: 1px solid {ORANGE};
            }}

            QPushButton#primaryButton:hover {{
                background-color: {ORANGE_HOVER};
                border: 1px solid {ORANGE_HOVER};
            }}

            QPushButton#primaryButton:pressed {{
                background-color: {ORANGE_PRESSED};
                border: 1px solid {ORANGE_PRESSED};
            }}

            QPushButton#secondaryButton {{
                background-color: {PANEL_2};
                color: {TEXT};
            }}

            QPushButton#secondaryButton:hover {{
                border: 1px solid {ORANGE};
            }}

            QPushButton:disabled {{
                background-color: {PANEL};
                color: #7C849A;
                border: 1px solid {BORDER};
            }}

            /* -------------------------
            TOOLTIP
            --------------------------*/
            QToolTip {{
                background-color: {PANEL};
                color: {TEXT};
                border: 1px solid {ORANGE};
                padding: 6px;
            }}
            """
        )



def main() -> None:
    """Application entry point."""
    app = QtWidgets.QApplication(sys.argv)

    # Optional: try to use a nicer font if available
    font = QtGui.QFont("Poppins", 10)
    if not QtGui.QFontInfo(font).family():
        font = QtGui.QFont("Segoe UI", 10)  # fallback
    app.setFont(font)

    window = MainWindow()
    window.showMaximized()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
