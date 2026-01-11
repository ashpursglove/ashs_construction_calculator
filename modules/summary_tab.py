"""
summary_tab.py

Summary / dashboard tab for the construction calculator suite.

This tab:
- Shows a consolidated overview of:
    * Blockwork cost
    * Sweet sand cost
    * Concrete works cost
    * Land preparation cost
    * Manpower cost
    * Equipment & machinery cost
    * Overall total project cost

- Shows key quantities where available (areas, volumes, hours, etc.).
- Exports a detailed multi-section PDF report with:
    * Cost summary
    * Per-discipline breakdowns
    * Manpower and equipment breakdown text from their tabs

The tab is intentionally defensive:
- It uses getattr(...) with defaults, so if a label is missing on any sub-tab
  it will show "N/A" instead of crashing.
"""

import os
import datetime

import sys
import subprocess
from typing import Optional, List

from PyQt5 import QtCore, QtWidgets


# Optional import of reportlab for PDF generation
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    from reportlab.lib import colors
except ImportError:  # pragma: no cover
    canvas = None  # type: ignore[misc]


class SummaryTab(QtWidgets.QWidget):
    """
    Summary / dashboard tab.

    It does NOT own the data. Instead it receives references to the
    other tabs and reads from their labels when "Refresh" or "Export"
    is pressed.

    Parameters
    ----------
    breeze_tab        : BreezeBlockTab
    sweet_sand_tab    : SweetSandTab
    concrete_tab      : ConcreteTab
    land_prep_tab     : LandPrepTab
    manpower_tab      : ManpowerTab
    equipment_tab     : EquipmentTab
    """

    def __init__(
        self,
        breeze_tab: QtWidgets.QWidget,
        sweet_sand_tab: QtWidgets.QWidget,
        concrete_tab: QtWidgets.QWidget,
        land_prep_tab: QtWidgets.QWidget,
        manpower_tab: QtWidgets.QWidget,
        equipment_tab: QtWidgets.QWidget,
        parent: Optional[QtWidgets.QWidget] = None,
    ) -> None:
        super().__init__(parent)

        # References to the other tabs
        self.breeze_tab = breeze_tab
        self.sweet_sand_tab = sweet_sand_tab
        self.concrete_tab = concrete_tab
        self.land_prep_tab = land_prep_tab
        self.manpower_tab = manpower_tab
        self.equipment_tab = equipment_tab

        # These will hold the last computed numeric totals
        self._cost_block = 0.0
        self._cost_sand = 0.0
        self._cost_concrete = 0.0
        self._cost_land_prep = 0.0
        self._cost_manpower = 0.0
        self._cost_equipment = 0.0
        self._cost_total = 0.0

        self._build_ui()
        self._connect_signals()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        """
        Build the summary UI.
        """

        outer_layout = QtWidgets.QVBoxLayout(self)
        outer_layout.setContentsMargins(12, 12, 12, 12)
        outer_layout.setSpacing(10)

        # ------------- Cost Summary Group -------------
        cost_group = QtWidgets.QGroupBox("Cost Summary", self)
        cost_form = QtWidgets.QFormLayout(cost_group)
        cost_form.setLabelAlignment(QtCore.Qt.AlignRight)

        self.lbl_blocks_cost = QtWidgets.QLabel("$0.00", cost_group)
        self.lbl_sand_cost = QtWidgets.QLabel("$0.00", cost_group)
        self.lbl_concrete_cost = QtWidgets.QLabel("$0.00", cost_group)
        self.lbl_land_prep_cost = QtWidgets.QLabel("$0.00", cost_group)
        self.lbl_manpower_cost = QtWidgets.QLabel("$0.00", cost_group)
        self.lbl_equipment_cost = QtWidgets.QLabel("$0.00", cost_group)
        self.lbl_total_cost = QtWidgets.QLabel("$0.00", cost_group)
        self.lbl_total_cost.setStyleSheet("font-weight: bold;")

        cost_form.addRow("Blockwork (breeze blocks):", self.lbl_blocks_cost)
        cost_form.addRow("Sweet sand (reactor base):", self.lbl_sand_cost)
        cost_form.addRow("Concrete works:", self.lbl_concrete_cost)
        cost_form.addRow("Land preparation:", self.lbl_land_prep_cost)
        cost_form.addRow("Manpower:", self.lbl_manpower_cost)
        cost_form.addRow("Equipment & machinery:", self.lbl_equipment_cost)
        cost_form.addRow("Total project cost:", self.lbl_total_cost)

        # ------------- Key Quantities Group -------------
        qty_group = QtWidgets.QGroupBox("Key Quantities (Read Only Snapshot)", self)
        qty_form = QtWidgets.QFormLayout(qty_group)
        qty_form.setLabelAlignment(QtCore.Qt.AlignRight)

        # These are all string labels – we just mirror what's on the other tabs
        self.lbl_block_area = QtWidgets.QLabel("N/A", qty_group)
        self.lbl_sand_volume = QtWidgets.QLabel("N/A", qty_group)
        self.lbl_concrete_volume = QtWidgets.QLabel("N/A", qty_group)

        # NEW: extra concrete snapshots (if available)
        self.lbl_concrete_formwork_area = QtWidgets.QLabel("N/A", qty_group)
        self.lbl_concrete_rebar = QtWidgets.QLabel("N/A", qty_group)

        self.lbl_land_cut_volume = QtWidgets.QLabel("N/A", qty_group)
        self.lbl_manhours = QtWidgets.QLabel("N/A", qty_group)
        self.lbl_equipment_hours = QtWidgets.QLabel("N/A", qty_group)

        qty_form.addRow("Total blockwork area:", self.lbl_block_area)
        qty_form.addRow("Sweet sand volume:", self.lbl_sand_volume)
        qty_form.addRow("Concrete volume:", self.lbl_concrete_volume)
        qty_form.addRow("Concrete formwork area:", self.lbl_concrete_formwork_area)
        qty_form.addRow("Concrete rebar quantity:", self.lbl_concrete_rebar)
        qty_form.addRow("Land prep cut volume:", self.lbl_land_cut_volume)
        qty_form.addRow("Total man-hours:", self.lbl_manhours)
        qty_form.addRow("Equipment operating hours:", self.lbl_equipment_hours)

        # ------------- Buttons -------------
        btn_layout = QtWidgets.QHBoxLayout()
        btn_layout.addStretch(1)

        self.refresh_button = QtWidgets.QPushButton("Refresh Summary", self)
        self.refresh_button.setObjectName("secondaryButton")

        self.export_button = QtWidgets.QPushButton("Export Report (PDF)", self)
        self.export_button.setObjectName("primaryButton")

        btn_layout.addWidget(self.refresh_button)
        btn_layout.addWidget(self.export_button)

        # ------------- Info note -------------
        note = QtWidgets.QLabel(
            "This summary is a snapshot of the other tabs. "
            "If you change inputs on those tabs, click 'Refresh Summary' "
            "to update these totals before exporting."
        )
        note.setWordWrap(True)

        # ------------- Assemble -------------
        outer_layout.addWidget(cost_group)
        outer_layout.addWidget(qty_group)
        outer_layout.addLayout(btn_layout)
        outer_layout.addWidget(note)
        outer_layout.addStretch(1)

    # ------------------------------------------------------------------
    # Signals
    # ------------------------------------------------------------------

    def _connect_signals(self) -> None:
        self.refresh_button.clicked.connect(self.refresh_summary)
        self.export_button.clicked.connect(self._on_export_report_clicked)

    # ------------------------------------------------------------------
    # Helper parsing functions
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_currency_label(lbl: Optional[QtWidgets.QLabel]) -> float:
        """
        Parse a QLabel containing a currency-like string such as:
        "$1,234.56" or "1,234.56 USD" into a float.

        Returns 0.0 if parsing fails or lbl is None.
        """
        if lbl is None:
            return 0.0

        text = lbl.text().strip()
        if not text:
            return 0.0

        # Remove common currency characters and commas
        for ch in ["$", "USD", ","]:
            text = text.replace(ch, "")

        text = text.strip()

        try:
            return float(text)
        except ValueError:
            return 0.0

    @staticmethod
    def _safe_label_text(widget: QtWidgets.QWidget, attr: str, default: str = "N/A") -> str:
        """
        Return the text of a QLabel named `attr` on `widget`,
        or default if it does not exist.
        """
        lbl = getattr(widget, attr, None)
        if isinstance(lbl, QtWidgets.QLabel):
            return lbl.text()
        return default

    # ------------------------------------------------------------------
    # Core: Refresh summary
    # ------------------------------------------------------------------

    def refresh_summary(self) -> None:
        """
        Pull values from all other tabs and update the summary labels.
        """

        # ------------ Blockwork cost ------------
        blocks_cost_lbl = getattr(self.breeze_tab, "lbl_total_cost", None)
        self._cost_block = self._parse_currency_label(blocks_cost_lbl)
        self.lbl_blocks_cost.setText(f"${self._cost_block:,.2f}")

        # Blockwork area
        self.lbl_block_area.setText(
            self._safe_label_text(self.breeze_tab, "lbl_total_area", "N/A")
        )

        # ------------ Sweet sand cost ------------
        sand_cost_lbl = getattr(self.sweet_sand_tab, "lbl_total_cost", None)
        self._cost_sand = self._parse_currency_label(sand_cost_lbl)
        self.lbl_sand_cost.setText(f"${self._cost_sand:,.2f}")

        # Sweet sand volume
        sand_volume = "N/A"
        for candidate in ["lbl_volume_total", "lbl_total_volume", "lbl_total_sand_volume", "lbl_total_volume_m3"]:
            sand_volume = self._safe_label_text(self.sweet_sand_tab, candidate, "N/A")
            if sand_volume != "N/A":
                break
        self.lbl_sand_volume.setText(sand_volume)

        # ------------ Concrete cost ------------
        concrete_cost_lbl = getattr(self.concrete_tab, "lbl_total_cost", None)
        self._cost_concrete = self._parse_currency_label(concrete_cost_lbl)
        self.lbl_concrete_cost.setText(f"${self._cost_concrete:,.2f}")

        # Concrete volume
        concrete_volume = "N/A"
        for candidate in ["lbl_volume", "lbl_concrete_volume", "lbl_total_concrete_volume", "lbl_concrete_vol"]:
            concrete_volume = self._safe_label_text(self.concrete_tab, candidate, "N/A")
            if concrete_volume != "N/A":
                break
        self.lbl_concrete_volume.setText(concrete_volume)

        # NEW: Concrete formwork area + rebar snapshot (defensive)
        concrete_form_area = "N/A"
        for candidate in ["lbl_form_area", "lbl_formwork_area", "lbl_concrete_form_area"]:
            concrete_form_area = self._safe_label_text(self.concrete_tab, candidate, "N/A")
            if concrete_form_area != "N/A":
                break
        self.lbl_concrete_formwork_area.setText(concrete_form_area)

        concrete_rebar = "N/A"
        for candidate in ["lbl_rebar_kg", "lbl_rebar_qty", "lbl_rebar"]:
            concrete_rebar = self._safe_label_text(self.concrete_tab, candidate, "N/A")
            if concrete_rebar != "N/A":
                break
        self.lbl_concrete_rebar.setText(concrete_rebar)

        # ------------ Land preparation cost ------------
        land_cost_lbl = getattr(self.land_prep_tab, "lbl_total_cost", None)
        self._cost_land_prep = self._parse_currency_label(land_cost_lbl)
        self.lbl_land_prep_cost.setText(f"${self._cost_land_prep:,.2f}")

        # Land cut volume
        self.lbl_land_cut_volume.setText(
            self._safe_label_text(self.land_prep_tab, "lbl_total_cut_volume", "N/A")
        )

        # ------------ Manpower cost ------------
        manpower_cost_lbl = getattr(self.manpower_tab, "lbl_grand_total", None)
        self._cost_manpower = self._parse_currency_label(manpower_cost_lbl)
        self.lbl_manpower_cost.setText(f"${self._cost_manpower:,.2f}")

        # Man-hours
        self.lbl_manhours.setText(
            self._safe_label_text(self.manpower_tab, "lbl_total_manhours", "N/A")
        )

        # ------------ Equipment cost ------------
        equipment_cost_lbl = getattr(self.equipment_tab, "lbl_grand_total", None)
        self._cost_equipment = self._parse_currency_label(equipment_cost_lbl)
        self.lbl_equipment_cost.setText(f"${self._cost_equipment:,.2f}")

        # Equipment hours
        self.lbl_equipment_hours.setText(
            self._safe_label_text(self.equipment_tab, "lbl_total_hours", "N/A")
        )

        # ------------ Total project cost ------------
        self._cost_total = (
            self._cost_block
            + self._cost_sand
            + self._cost_concrete
            + self._cost_land_prep
            + self._cost_manpower
            + self._cost_equipment
        )
        self.lbl_total_cost.setText(f"${self._cost_total:,.2f}")

    # ------------------------------------------------------------------
    # Export report
    # ------------------------------------------------------------------

    def _on_export_report_clicked(self) -> None:
        """
        Export a PDF report to a user-chosen filename/location and auto-open it.
        """
        # Always refresh before exporting
        self.refresh_summary()

        if canvas is None:
            QtWidgets.QMessageBox.warning(
                self,
                "ReportLab Not Installed",
                "The 'reportlab' package is required to generate PDF reports.\n\n"
                "Install it with:\n"
                "    pip install reportlab",
            )
            return

        # Default filename with timestamp
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        default_name = f"Ash's Construction_Planner_Report_{timestamp}.pdf"

        # Remember the last used directory (falls back to current working dir)
        start_dir = getattr(self, "_last_export_dir", os.getcwd())
        default_path = os.path.join(start_dir, default_name)

        selected_path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self,
            "Save PDF Report",
            default_path,
            "PDF Files (*.pdf)",
        )

        if not selected_path:
            return

        if not selected_path.lower().endswith(".pdf"):
            selected_path += ".pdf"

        self._last_export_dir = os.path.dirname(selected_path)

        try:
            self._write_pdf(selected_path)
        except Exception as exc:  # pragma: no cover
            QtWidgets.QMessageBox.critical(
                self,
                "Error Generating Report",
                f"An error occurred while creating the PDF:\n{exc}",
            )
            return

        try:
            self._open_file(selected_path)
        except Exception:
            QtWidgets.QMessageBox.information(
                self,
                "Report Generated",
                f"Report saved to:\n{selected_path}",
            )

    def _write_pdf(self, path: str) -> None:
        """
        Generate a detailed multi-section PDF file at the given path,
        styled to match the app's signature dark navy + orange theme.
        """

        c = canvas.Canvas(path, pagesize=A4)
        c.setTitle("Construction Report")
        width, height = A4

        margin = 40
        y = height - margin

        # Theme colours
        BG = colors.HexColor("#050B1A")          # deep navy background
        BORDER = colors.HexColor("#223056")      # subtle borders/lines
        TEXT = colors.HexColor("#F5F5F5")        # main text
        TEXT_DIM = colors.HexColor("#A9B0C5")    # secondary text
        ORANGE = colors.HexColor("#FF7A00")      # signature accent

        def paint_page_background() -> None:
            c.saveState()
            c.setFillColor(BG)
            c.rect(0, 0, width, height, stroke=0, fill=1)
            c.restoreState()

        paint_page_background()

        def new_page() -> None:
            nonlocal y
            c.showPage()
            paint_page_background()
            y = height - margin

        def hline(offset: int = 8) -> None:
            nonlocal y
            line_y = y - offset
            if line_y < margin + 20:
                new_page()
                line_y = y - offset

            c.setStrokeColor(BORDER)
            c.setLineWidth(0.8)
            c.line(margin, line_y, width - margin, line_y)
            y = line_y - 10

        def line(text: str = "", fontsize: int = 10, dy: int = 14, dim: bool = False) -> None:
            nonlocal y
            if y < margin + 40:
                new_page()

            if text:
                c.setFont("Helvetica", fontsize)
                c.setFillColor(TEXT_DIM if dim else TEXT)
                c.drawString(margin, y, text)

            y -= dy

        def paragraph(lines, fontsize: int = 10, dy: int = 14, dim: bool = False) -> None:
            for t in lines:
                line(t, fontsize=fontsize, dy=dy, dim=dim)

        def section_header(title: str) -> None:
            nonlocal y
            bar_height = 20

            if y < margin + bar_height + 30:
                new_page()

            c.setFillColor(ORANGE)
            c.setStrokeColor(ORANGE)
            c.roundRect(
                margin,
                y - bar_height + 4,
                width - 2 * margin,
                bar_height,
                6,
                stroke=0,
                fill=1,
            )

            c.setFillColor(BG)
            c.setFont("Helvetica-Bold", 11)
            c.drawString(margin + 8, y - bar_height + 9, title)

            y -= bar_height + 14
            c.setFillColor(TEXT)

        # Header
        c.setFont("Helvetica-Bold", 18)
        c.setFillColor(ORANGE)
        c.drawString(margin, y, "Construction Project Detailed Cost Report")
        y -= 22

        c.setFont("Helvetica", 9)
        c.setFillColor(TEXT_DIM)
        c.drawString(margin, y, "Generated by Ash's Construction Planner")
        y -= 18

        hline()

        # 1) Cost Summary
        section_header("1. Cost Summary")

        paragraph(
            [
                f"1.1 Blockwork (breeze blocks):      {self.lbl_blocks_cost.text()}",
                f"1.2 Sweet sand (reactor base):      {self.lbl_sand_cost.text()}",
                f"1.3 Concrete works:                 {self.lbl_concrete_cost.text()}",
                f"1.4 Land preparation:               {self.lbl_land_prep_cost.text()}",
                f"1.5 Manpower:                       {self.lbl_manpower_cost.text()}",
                f"1.6 Equipment & machinery:          {self.lbl_equipment_cost.text()}",
            ],
            fontsize=10,
            dy=14,
        )

        line()
        c.setFont("Helvetica-Bold", 12)
        c.setFillColor(ORANGE)
        c.drawString(margin, y, f"1.7 TOTAL PROJECT COST:             {self.lbl_total_cost.text()}")
        c.setFillColor(TEXT)
        y -= 20

        hline()

        # 2) Blockwork Breakdown
        section_header("2. Blockwork (Breeze Blocks)")

        block_area_total = self.lbl_block_area.text()
        wall_area = self._safe_label_text(self.breeze_tab, "lbl_wall_area", "N/A")
        arc_area = self._safe_label_text(self.breeze_tab, "lbl_arc_area", "N/A")
        reactor_area = self._safe_label_text(self.breeze_tab, "lbl_reactor_area", "N/A")

        lbl_blocks = getattr(self.breeze_tab, "lbl_blocks", None)
        lbl_pallets = getattr(self.breeze_tab, "lbl_pallets", None)
        lbl_leftover = getattr(self.breeze_tab, "lbl_leftover", None)

        blocks_text = lbl_blocks.text() if isinstance(lbl_blocks, QtWidgets.QLabel) else "N/A"
        pallets_text = lbl_pallets.text() if isinstance(lbl_pallets, QtWidgets.QLabel) else "N/A"
        leftover_text = lbl_leftover.text() if isinstance(lbl_leftover, QtWidgets.QLabel) else "N/A"

        paragraph(
            [
                f"2.1 Total blockwork area:           {block_area_total}",
                f"2.2 Straight walls area:            {wall_area}",
                f"2.3 Half-circle arcs area:          {arc_area}",
                f"2.4 Raceway reactor walls area:     {reactor_area}",
                "",
                f"2.5 Blocks required:                {blocks_text}",
                f"2.6 Pallets required:               {pallets_text}",
                f"2.7 Leftover blocks (last pallet):  {leftover_text}",
            ],
            fontsize=10,
            dy=14,
        )

        hline()

        # 3) Sweet Sand Breakdown
        section_header("3. Sweet Sand (Reactor Base Fill)")
        paragraph(
            [
                f"3.1 Total sweet sand cost:          {self.lbl_sand_cost.text()}",
                f"3.2 Sweet sand volume:              {self.lbl_sand_volume.text()}",
            ],
            fontsize=10,
            dy=14,
        )
        hline()

        # 4) Concrete Works Breakdown (UPDATED)
        section_header("4. Concrete Works")

        concrete_volume = self.lbl_concrete_volume.text()
        concrete_weight = self._safe_label_text(self.concrete_tab, "lbl_conc_weight", "N/A")
        concrete_form_area = self._safe_label_text(self.concrete_tab, "lbl_form_area", "N/A")
        rebar_kg = self._safe_label_text(self.concrete_tab, "lbl_rebar_kg", "N/A")
        rebar_t = self._safe_label_text(self.concrete_tab, "lbl_rebar_tons", "N/A")

        conc_cost = self._safe_label_text(self.concrete_tab, "lbl_conc_cost", "N/A")
        rebar_cost = self._safe_label_text(self.concrete_tab, "lbl_rebar_cost", "N/A")
        formwork_cost = self._safe_label_text(self.concrete_tab, "lbl_formwork_cost", "N/A")

        paragraph(
            [
                f"4.1 Total concrete works cost (tab total): {self.lbl_concrete_cost.text()}",
                "",
                "4.2 Key quantities:",
                f"      • Concrete volume:            {concrete_volume}",
                f"      • Concrete weight:            {concrete_weight}",
                f"      • Rebar quantity:             {rebar_kg} ({rebar_t})",
                f"      • Formwork area (vertical):   {concrete_form_area}",
                "",
                "4.3 Cost breakdown (if available on tab):",
                f"      • Concrete cost:              {conc_cost}",
                f"      • Rebar cost:                 {rebar_cost}",
                f"      • Formwork cost:              {formwork_cost}",
            ],
            fontsize=10,
            dy=14,
        )
        hline()

        # 5) Land Preparation Breakdown
        section_header("5. Land Preparation")
        paragraph(
            [
                f"5.1 Total land preparation cost:    {self.lbl_land_prep_cost.text()}",
                f"5.2 Total cut volume:               {self.lbl_land_cut_volume.text()}",
            ],
            fontsize=10,
            dy=14,
        )
        hline()

        # 6) Manpower Breakdown
        section_header("6. Manpower")
        manhours = self.lbl_manhours.text()
        paragraph(
            [
                f"6.1 Total manpower cost:            {self.lbl_manpower_cost.text()}",
                f"6.2 Total man-hours:                {manhours}",
                "",
                "6.3 Notes:",
                "      • Uses your tab totals (refresh the tab before exporting for best results).",
            ],
            fontsize=10,
            dy=14,
        )
        hline()

        # 7) Equipment Breakdown
        section_header("7. Equipment & Machinery")
        equipment_hours = self.lbl_equipment_hours.text()
        fuel_litres = self._safe_label_text(self.equipment_tab, "lbl_total_fuel", "N/A")
        fuel_cost = self._safe_label_text(self.equipment_tab, "lbl_total_fuel_cost", "N/A")
        equipment_cost = self.lbl_equipment_cost.text()
        mob_cost = self._safe_label_text(self.equipment_tab, "lbl_mob_cost", "N/A")
        overhead_cost = self._safe_label_text(self.equipment_tab, "lbl_overhead_cost", "N/A")

        paragraph(
            [
                "7.1 Totals:",
                f"      • Operating hours (all machines): {equipment_hours}",
                f"      • Total equipment cost:           {equipment_cost}",
                "",
                "7.2 Fuel & overheads:",
                f"      • Fuel consumption:              {fuel_litres}",
                f"      • Fuel cost:                     {fuel_cost}",
                f"      • Mobilisation + demob:          {mob_cost}",
                f"      • Plant overhead + misc:         {overhead_cost}",
                "",
            ],
            fontsize=10,
            dy=14,
        )

        equip_breakdown_widget = getattr(self.equipment_tab, "breakdown_text", None)
        equip_breakdown_lines = []
        if isinstance(equip_breakdown_widget, QtWidgets.QPlainTextEdit):
            text = equip_breakdown_widget.toPlainText()
            if text.strip():
                equip_breakdown_lines = text.splitlines()

        if equip_breakdown_lines:
            line("7.3 Per-equipment breakdown:", fontsize=11, dy=16)
            for row in equip_breakdown_lines:
                line(row, fontsize=8, dy=11, dim=True)
        else:
            line("7.3 Per-equipment breakdown not available (no calculation yet).", fontsize=9, dy=14, dim=True)

        hline()

        # 8) Closing Notes
        section_header("8. Notes & Assumptions")
        paragraph(
            [
                "- This is an internal report for internal use and estimates only.",
                "- For final design and construction, verify quantities, unit rates,",
                "  and assumptions with detailed engineering drawings and site conditions.",
            ],
            fontsize=9,
            dy=12,
            dim=True,
        )

        c.showPage()
        c.save()

    # ------------------------------------------------------------------
    # File opening helper
    # ------------------------------------------------------------------

    @staticmethod
    def _open_file(path: str) -> None:
        """
        Open the file at 'path' with the OS default application.
        Supports Windows, macOS, Linux (xdg-open).
        """
        if sys.platform.startswith("win"):
            os.startfile(path)  # type: ignore[attr-defined]
        elif sys.platform.startswith("darwin"):
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen(["xdg-open", path])
