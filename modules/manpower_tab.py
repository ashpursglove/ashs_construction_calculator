"""
manpower_tab.py

PyQt5 widget implementing a manpower and labour cost calculator for
typical construction trades.

The tab lets you:
- Define workforce by trade (headcount + hourly rate).
- Define working pattern (days, hours, overtime).
- Define mobilisation / demobilisation and site overhead costs.
- Calculate:
    * Man-hours per trade and in total.
    * Labour cost per trade and in total.
    * Overheads and mobilisation costs.
    * Grand total cost.

High-level model
----------------
Trades
    A fixed list of common site trades is provided:
        - General Labourer
        - Carpenter / Formwork
        - Steel Fixer
        - Concrete Crew / Finisher
        - Mason / Block Layer
        - Electrician
        - Plumber / Pipefitter
        - Equipment Operator
        - Foreman / Supervisor
        - Site Engineer / Manager
        - Safety Officer / HSE

    For each trade:
        - n_workers          [headcount]
        - rate_hour          [USD/hour]

Schedule
    - days                 [working days]
    - hours_normal_per_day [h/day]
    - hours_ot_per_day     [h/day]
    - ot_factor            [-]: multiplier on base rate for overtime

    Man-hours per trade:
        MH_trade = n_workers * days * (hours_normal_per_day + hours_ot_per_day)

    Labour cost per trade:
        Cost_normal = n_workers * days * hours_normal_per_day * rate_hour
        Cost_ot     = n_workers * days * hours_ot_per_day * rate_hour * ot_factor
        Cost_trade  = Cost_normal + Cost_ot

Overheads and mobilisation
    - mobilisation_lump     [USD]
    - demobilisation_lump   [USD]
    - site_overhead_daily   [USD/day]
    - misc_allowance        [USD]

    Overhead cost:
        Cost_overhead = site_overhead_daily * days

    Total project manpower-related cost:
        Cost_total = sum(Cost_trade) + mobilisation_lump + demobilisation_lump
                     + Cost_overhead + misc_allowance
"""

from typing import Optional, List, Tuple

from PyQt5 import QtCore, QtWidgets


class ManpowerTab(QtWidgets.QWidget):
    """
    Main widget for the manpower calculator tab.
    Designed to be dropped into a QTabWidget.
    Wrapped in a QScrollArea so it works on smaller screens.
    """








    # ------------------------------------------------------------------
    # Project Save/Load
    # ------------------------------------------------------------------

    def export_state(self) -> dict:
        workforce = []
        for i in range(len(self.trades)):
            workforce.append(
                {
                    "trade": self.trades[i],
                    "workers": int(self.worker_spin_boxes[i].value()),
                    "rate": float(self.rate_spin_boxes[i].value()),
                }
            )

        return {
            "workforce": workforce,
            "days": int(self.days_spin.value()),
            "hours_normal": float(self.hours_normal_spin.value()),
            "hours_ot": float(self.hours_ot_spin.value()),
            "ot_factor": float(self.ot_factor_spin.value()),
            "mobilisation": float(self.mobilisation_spin.value()),
            "demobilisation": float(self.demobilisation_spin.value()),
            "daily_overhead": float(self.daily_overhead_spin.value()),
            "misc_allowance": float(self.misc_allowance_spin.value()),
        }

    def import_state(self, state: dict) -> None:
        if not isinstance(state, dict):
            return

        # Workforce table
        workforce = state.get("workforce", [])
        if isinstance(workforce, list):
            # Match by index (stable), and fall back to whatever exists
            for i in range(min(len(workforce), len(self.trades))):
                row = workforce[i]
                if isinstance(row, dict):
                    self.worker_spin_boxes[i].setValue(int(row.get("workers", 0)))
                    self.rate_spin_boxes[i].setValue(float(row.get("rate", self.rate_spin_boxes[i].value())))

        # Schedule
        self.days_spin.setValue(int(state.get("days", self.days_spin.value())))
        self.hours_normal_spin.setValue(float(state.get("hours_normal", self.hours_normal_spin.value())))
        self.hours_ot_spin.setValue(float(state.get("hours_ot", self.hours_ot_spin.value())))
        self.ot_factor_spin.setValue(float(state.get("ot_factor", self.ot_factor_spin.value())))

        # Overheads
        self.mobilisation_spin.setValue(float(state.get("mobilisation", self.mobilisation_spin.value())))
        self.demobilisation_spin.setValue(float(state.get("demobilisation", self.demobilisation_spin.value())))
        self.daily_overhead_spin.setValue(float(state.get("daily_overhead", self.daily_overhead_spin.value())))
        self.misc_allowance_spin.setValue(float(state.get("misc_allowance", self.misc_allowance_spin.value())))




    def __init__(self, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        self.trades: List[str] = [
            "General Labourer",
            "Carpenter / Formwork",
            "Steel Fixer",
            "Concrete Crew / Finisher",
            "Mason / Block Layer",
            "Electrician",
            "Plumber / Pipefitter",
            "Equipment Operator",
            "Foreman / Supervisor",
            "Site Engineer / Manager",
            "Safety Officer / HSE",
        ]
        self.worker_spin_boxes: List[QtWidgets.QSpinBox] = []
        self.rate_spin_boxes: List[QtWidgets.QDoubleSpinBox] = []

        self._build_ui()
        self._connect_signals()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        """
        Build the UI with a scrollable content area.
        """
        outer_layout = QtWidgets.QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)

        scroll_area = QtWidgets.QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QtWidgets.QFrame.NoFrame)

        content_widget = QtWidgets.QWidget(scroll_area)
        content_layout = QtWidgets.QVBoxLayout(content_widget)
        content_layout.setContentsMargins(12, 12, 12, 12)
        content_layout.setSpacing(10)

        # ---------------- Workforce / trades ----------------
        workforce_group = QtWidgets.QGroupBox("Workforce by Trade", content_widget)
        workforce_layout = QtWidgets.QVBoxLayout(workforce_group)

        workforce_desc = QtWidgets.QLabel(
            "Define the number of workers and hourly rate for each trade. "
            "If a trade is not used, leave the worker count at 0."
        )
        workforce_desc.setWordWrap(True)
        workforce_layout.addWidget(workforce_desc)

        # Table-like layout (no QTableWidget to keep it simple and well-typed)
        grid = QtWidgets.QGridLayout()
        grid.setColumnStretch(0, 3)
        grid.setColumnStretch(1, 1)
        grid.setColumnStretch(2, 1)
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(4)

        header_trade = QtWidgets.QLabel("Trade")
        header_workers = QtWidgets.QLabel("Workers")
        header_rate = QtWidgets.QLabel("Rate (USD/h)")
        header_trade.setStyleSheet("font-weight: bold;")
        header_workers.setStyleSheet("font-weight: bold;")
        header_rate.setStyleSheet("font-weight: bold;")

        grid.addWidget(header_trade, 0, 0)
        grid.addWidget(header_workers, 0, 1)
        grid.addWidget(header_rate, 0, 2)

        # Reasonable default rates (USD/h) – adjust to your own reality
        default_rates = [
            5.0,   # General Labourer
            7.0,   # Carpenter / Formwork
            7.5,   # Steel Fixer
            6.5,   # Concrete Crew / Finisher
            6.5,   # Mason / Block Layer
            8.0,   # Electrician
            7.5,   # Plumber / Pipefitter
            8.0,   # Equipment Operator
            10.0,  # Foreman / Supervisor
            12.0,  # Site Engineer / Manager
            9.0,   # Safety Officer / HSE
        ]

        for row, trade in enumerate(self.trades, start=1):
            trade_label = QtWidgets.QLabel(trade)
            grid.addWidget(trade_label, row, 0)

            worker_spin = QtWidgets.QSpinBox(workforce_group)
            worker_spin.setRange(0, 10_000)
            worker_spin.setValue(0)
            grid.addWidget(worker_spin, row, 1)

            rate_spin = QtWidgets.QDoubleSpinBox(workforce_group)
            rate_spin.setSuffix(" $/h")
            rate_spin.setDecimals(2)
            rate_spin.setRange(0.0, 1000.0)
            rate_spin.setSingleStep(0.5)
            rate_spin.setValue(default_rates[row - 1])
            grid.addWidget(rate_spin, row, 2)

            self.worker_spin_boxes.append(worker_spin)
            self.rate_spin_boxes.append(rate_spin)

        workforce_layout.addLayout(grid)

        # ---------------- Schedule ----------------
        schedule_group = QtWidgets.QGroupBox("Schedule and Working Pattern", content_widget)
        schedule_form = QtWidgets.QFormLayout(schedule_group)
        schedule_form.setLabelAlignment(QtCore.Qt.AlignRight)

        self.days_spin = QtWidgets.QSpinBox(schedule_group)
        self.days_spin.setRange(1, 3650)  # up to ~10 years if you really want
        self.days_spin.setValue(30)

        self.hours_normal_spin = QtWidgets.QDoubleSpinBox(schedule_group)
        self.hours_normal_spin.setSuffix(" h/day")
        self.hours_normal_spin.setDecimals(1)
        self.hours_normal_spin.setRange(0.0, 24.0)
        self.hours_normal_spin.setSingleStep(0.5)
        self.hours_normal_spin.setValue(8.0)

        self.hours_ot_spin = QtWidgets.QDoubleSpinBox(schedule_group)
        self.hours_ot_spin.setSuffix(" h/day")
        self.hours_ot_spin.setDecimals(1)
        self.hours_ot_spin.setRange(0.0, 24.0)
        self.hours_ot_spin.setSingleStep(0.5)
        self.hours_ot_spin.setValue(0.0)

        self.ot_factor_spin = QtWidgets.QDoubleSpinBox(schedule_group)
        self.ot_factor_spin.setDecimals(2)
        self.ot_factor_spin.setRange(1.0, 5.0)
        self.ot_factor_spin.setSingleStep(0.1)
        self.ot_factor_spin.setValue(1.5)

        schedule_form.addRow("Working days:", self.days_spin)
        schedule_form.addRow("Normal hours per day:", self.hours_normal_spin)
        schedule_form.addRow("Overtime hours per day:", self.hours_ot_spin)
        schedule_form.addRow("Overtime factor:", self.ot_factor_spin)

        schedule_note = QtWidgets.QLabel(
            "Overtime factor multiplies the base hourly rate for overtime hours. "
            "For example, 1.5 means overtime is paid at time-and-a-half."
        )
        schedule_note.setWordWrap(True)

        # ---------------- Mobilisation & overheads ----------------
        overhead_group = QtWidgets.QGroupBox("Mobilisation, Overheads and Allowances", content_widget)
        overhead_form = QtWidgets.QFormLayout(overhead_group)
        overhead_form.setLabelAlignment(QtCore.Qt.AlignRight)

        self.mobilisation_spin = QtWidgets.QDoubleSpinBox(overhead_group)
        self.mobilisation_spin.setSuffix(" USD")
        self.mobilisation_spin.setDecimals(2)
        self.mobilisation_spin.setRange(0.0, 1_000_000.0)
        self.mobilisation_spin.setSingleStep(100.0)
        self.mobilisation_spin.setValue(0.0)

        self.demobilisation_spin = QtWidgets.QDoubleSpinBox(overhead_group)
        self.demobilisation_spin.setSuffix(" USD")
        self.demobilisation_spin.setDecimals(2)
        self.demobilisation_spin.setRange(0.0, 1_000_000.0)
        self.demobilisation_spin.setSingleStep(100.0)
        self.demobilisation_spin.setValue(0.0)

        self.daily_overhead_spin = QtWidgets.QDoubleSpinBox(overhead_group)
        self.daily_overhead_spin.setSuffix(" USD/day")
        self.daily_overhead_spin.setDecimals(2)
        self.daily_overhead_spin.setRange(0.0, 1_000_000.0)
        self.daily_overhead_spin.setSingleStep(50.0)
        self.daily_overhead_spin.setValue(0.0)

        self.misc_allowance_spin = QtWidgets.QDoubleSpinBox(overhead_group)
        self.misc_allowance_spin.setSuffix(" USD")
        self.misc_allowance_spin.setDecimals(2)
        self.misc_allowance_spin.setRange(0.0, 1_000_000.0)
        self.misc_allowance_spin.setSingleStep(100.0)
        self.misc_allowance_spin.setValue(0.0)

        overhead_form.addRow("Mobilisation lump sum:", self.mobilisation_spin)
        overhead_form.addRow("Demobilisation lump sum:", self.demobilisation_spin)
        overhead_form.addRow("Daily site overhead:", self.daily_overhead_spin)
        overhead_form.addRow("Misc / contingency:", self.misc_allowance_spin)

        overhead_note = QtWidgets.QLabel(
            "Mobilisation and demobilisation can cover visas, travel, camp setup, "
            "equipment arrival, etc. Daily site overhead is for office, welfare, "
            "site management overheads that scale with time. Misc/contingency is a "
            "flexible lump sum for small items and risk."
        )
        overhead_note.setWordWrap(True)

        # ---------------- Buttons ----------------
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addStretch(1)

        self.reset_button = QtWidgets.QPushButton("Reset", content_widget)
        self.reset_button.setObjectName("secondaryButton")

        self.calculate_button = QtWidgets.QPushButton("Calculate", content_widget)
        self.calculate_button.setObjectName("primaryButton")

        button_layout.addWidget(self.reset_button)
        button_layout.addWidget(self.calculate_button)

        # ---------------- Results ----------------
        result_group = QtWidgets.QGroupBox("Results", content_widget)
        result_form = QtWidgets.QFormLayout(result_group)
        result_form.setLabelAlignment(QtCore.Qt.AlignRight)

        self.lbl_total_manhours = QtWidgets.QLabel("0.0 h", result_group)
        self.lbl_total_labour_cost = QtWidgets.QLabel("$0.00", result_group)
        self.lbl_overhead_cost = QtWidgets.QLabel("$0.00", result_group)
        self.lbl_mob_cost = QtWidgets.QLabel("$0.00", result_group)
        self.lbl_grand_total = QtWidgets.QLabel("$0.00", result_group)

        result_form.addRow("Total man-hours (all trades):", self.lbl_total_manhours)
        result_form.addRow("Total labour cost:", self.lbl_total_labour_cost)
        result_form.addRow("Mobilisation + demobilisation:", self.lbl_mob_cost)
        result_form.addRow("Overhead + misc cost:", self.lbl_overhead_cost)
        result_form.addRow("Grand total cost:", self.lbl_grand_total)

        # Breakdown text area
        self.breakdown_text = QtWidgets.QPlainTextEdit(result_group)
        self.breakdown_text.setReadOnly(True)
        self.breakdown_text.setPlaceholderText(
            "Per-trade breakdown will appear here after calculation."
        )
        result_form.addRow("Per-trade breakdown:", self.breakdown_text)

        # ---------------- Assemble content layout ----------------
        content_layout.addWidget(workforce_group)
        content_layout.addWidget(schedule_group)
        content_layout.addWidget(schedule_note)
        content_layout.addWidget(overhead_group)
        content_layout.addWidget(overhead_note)
        content_layout.addLayout(button_layout)
        content_layout.addWidget(result_group)
        content_layout.addStretch(1)

        scroll_area.setWidget(content_widget)
        outer_layout.addWidget(scroll_area)

    # ------------------------------------------------------------------
    # Signal wiring
    # ------------------------------------------------------------------

    def _connect_signals(self) -> None:
        """Connect signals to slots."""
        self.calculate_button.clicked.connect(self._on_calculate_clicked)
        self.reset_button.clicked.connect(self._on_reset_clicked)

    # ------------------------------------------------------------------
    # Core logic
    # ------------------------------------------------------------------

    def _on_calculate_clicked(self) -> None:
        """
        Calculate man-hours and costs for all trades
        plus mobilisation and overheads.
        """
        days = int(self.days_spin.value())
        hours_normal = float(self.hours_normal_spin.value())
        hours_ot = float(self.hours_ot_spin.value())
        ot_factor = float(self.ot_factor_spin.value())

        mobilisation = float(self.mobilisation_spin.value())
        demobilisation = float(self.demobilisation_spin.value())
        daily_overhead = float(self.daily_overhead_spin.value())
        misc_allowance = float(self.misc_allowance_spin.value())

        if days <= 0:
            QtWidgets.QMessageBox.warning(
                self,
                "Invalid Input",
                "Working days must be greater than zero.",
            )
            return

        if hours_normal < 0 or hours_ot < 0:
            QtWidgets.QMessageBox.warning(
                self,
                "Invalid Input",
                "Working hours cannot be negative.",
            )
            return

        if ot_factor < 1.0:
            QtWidgets.QMessageBox.warning(
                self,
                "Invalid Input",
                "Overtime factor should be at least 1.0.",
            )
            return

        total_manhours = 0.0
        total_labour_cost = 0.0

        breakdown_lines: List[str] = []
        breakdown_lines.append(
            f"Schedule: {days} days, {hours_normal:.1f} h/day normal, "
            f"{hours_ot:.1f} h/day overtime at x{ot_factor:.2f}.\n"
        )
        breakdown_lines.append("Per-trade details:")
        breakdown_lines.append(
            "Trade | Workers | Man-hours | Labour cost (USD)"
        )
        breakdown_lines.append("-" * 60)

        # Per-trade calculations
        for idx, trade in enumerate(self.trades):
            n_workers = int(self.worker_spin_boxes[idx].value())
            rate = float(self.rate_spin_boxes[idx].value())

            if n_workers <= 0 or rate <= 0:
                # If either is zero, we treat the trade as inactive.
                continue

            manhours_trade = n_workers * days * (hours_normal + hours_ot)

            cost_normal = n_workers * days * hours_normal * rate
            cost_ot = n_workers * days * hours_ot * rate * ot_factor
            cost_trade = cost_normal + cost_ot

            total_manhours += manhours_trade
            total_labour_cost += cost_trade

            breakdown_lines.append(
                f"{trade} | {n_workers} | {manhours_trade:,.1f} h | ${cost_trade:,.2f}"
            )

        # Mobilisation, overheads, grand total
        mob_cost = mobilisation + demobilisation
        overhead_cost = daily_overhead * days + misc_allowance
        grand_total = total_labour_cost + mob_cost + overhead_cost

        # Update labels
        self.lbl_total_manhours.setText(f"{total_manhours:,.1f} h")
        self.lbl_total_labour_cost.setText(f"${total_labour_cost:,.2f}")
        self.lbl_mob_cost.setText(f"${mob_cost:,.2f}")
        self.lbl_overhead_cost.setText(f"${overhead_cost:,.2f}")
        self.lbl_grand_total.setText(f"${grand_total:,.2f}")

        # Add summary lines for overheads and totals
        breakdown_lines.append("")
        breakdown_lines.append(
            f"Total labour cost: ${total_labour_cost:,.2f}"
        )
        breakdown_lines.append(
            f"Mobilisation + demobilisation: ${mob_cost:,.2f}"
        )
        breakdown_lines.append(
            f"Overhead + misc: ${overhead_cost:,.2f}"
        )
        breakdown_lines.append(
            f"Grand total manpower-related cost: ${grand_total:,.2f}"
        )

        self.breakdown_text.setPlainText("\n".join(breakdown_lines))

    def _on_reset_clicked(self) -> None:
        """Reset all inputs and outputs to defaults."""

        # Reset workers and keep default rates
        for spin in self.worker_spin_boxes:
            spin.setValue(0)

        self.days_spin.setValue(30)
        self.hours_normal_spin.setValue(8.0)
        self.hours_ot_spin.setValue(0.0)
        self.ot_factor_spin.setValue(1.5)

        self.mobilisation_spin.setValue(0.0)
        self.demobilisation_spin.setValue(0.0)
        self.daily_overhead_spin.setValue(0.0)
        self.misc_allowance_spin.setValue(0.0)

        self.lbl_total_manhours.setText("0.0 h")
        self.lbl_total_labour_cost.setText("$0.00")
        self.lbl_mob_cost.setText("$0.00")
        self.lbl_overhead_cost.setText("$0.00")
        self.lbl_grand_total.setText("$0.00")
        self.breakdown_text.clear()
        self.breakdown_text.setPlaceholderText(
            "Per-trade breakdown will appear here after calculation."
        )
