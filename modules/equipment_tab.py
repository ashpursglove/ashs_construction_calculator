"""
equipment_tab.py

PyQt5 widget implementing an Equipment & Machinery costing tab.

This tab lets you:
- Define multiple pieces of equipment (name, count, hourly rate, fuel burn, utilisation).
- Define a global operating schedule (days and operating hours per day).
- Define a global fuel price.
- Define mobilisation/demobilisation and daily plant overheads.

The tab then calculates, per equipment row and in total:
- Operating man-hours of machines.
- Fuel consumption (litres).
- Hire cost (USD).
- Fuel cost (USD).
- Mobilisation + demobilisation + overhead + misc.
- Grand total equipment-related cost.

High-level model
----------------
For each equipment item i:
    Inputs:
        name_i              : description (e.g. "20t Excavator")
        n_units_i           : number of identical units [count]
        rate_hour_i         : hire rate per operating hour [USD/h]
        fuel_lph_i          : fuel consumption per operating hour [L/h]
        utilisation_pct_i   : utilisation of schedule [% of time actually working]

Global schedule:
    days                   : number of working days
    hours_per_day          : machine hours available per day

Global fuel:
    fuel_price             : price per litre [USD/L]

Per-equipment calculations:
    hours_schedule = days * hours_per_day
    hours_effective_i = n_units_i * hours_schedule * (utilisation_pct_i / 100)

    hire_cost_i = hours_effective_i * rate_hour_i
    fuel_litres_i = hours_effective_i * fuel_lph_i
    fuel_cost_i = fuel_litres_i * fuel_price

Totals:
    hours_total       = sum_i hours_effective_i
    hire_cost_total   = sum_i hire_cost_i
    fuel_litres_total = sum_i fuel_litres_i
    fuel_cost_total   = sum_i fuel_cost_i

Overheads & mobilisation:
    mobilisation_lump   [USD]
    demobilisation_lump [USD]
    daily_plant_over    [USD/day]
    misc_plant_allow    [USD]

    overhead_cost = daily_plant_over * days
    mob_cost      = mobilisation_lump + demobilisation_lump

Grand total:
    cost_total = hire_cost_total + fuel_cost_total + mob_cost + overhead_cost + misc_plant_allow
"""

from typing import Optional, List

from PyQt5 import QtCore, QtWidgets


class EquipmentTab(QtWidgets.QWidget):
    """
    Main widget for the Equipment & Machinery costing tab.
    Designed to be dropped into a QTabWidget.
    Wrapped in a QScrollArea for smaller screens.
    """













    # ------------------------------------------------------------------
    # Project Save/Load
    # ------------------------------------------------------------------

    def export_state(self) -> dict:
        rows = []
        for i in range(len(self.equip_name_edits)):
            rows.append(
                {
                    "name": self.equip_name_edits[i].text(),
                    "count": int(self.equip_count_spins[i].value()),
                    "hire_rate_day": float(self.equip_rate_spins[i].value()),
                    "fuel_lph": float(self.equip_fuel_spins[i].value()),
                    "util_pct": float(self.equip_util_spins[i].value()),
                }
            )

        return {
            "rows": rows,
            "days": int(self.days_spin.value()),
            "hours_per_day": float(self.hours_per_day_spin.value()),
            "fuel_price": float(self.fuel_price_spin.value()),
            "mobilisation": float(self.mobilisation_spin.value()),
            "demobilisation": float(self.demobilisation_spin.value()),
            "daily_plant_overhead": float(self.daily_plant_overhead_spin.value()),
            "misc_plant_allow": float(self.misc_plant_allow_spin.value()),
        }

    def import_state(self, state: dict) -> None:
        if not isinstance(state, dict):
            return

        rows = state.get("rows", [])
        if isinstance(rows, list):
            for i in range(min(len(rows), len(self.equip_name_edits))):
                row = rows[i]
                if not isinstance(row, dict):
                    continue

                self.equip_name_edits[i].setText(str(row.get("name", self.equip_name_edits[i].text())))
                self.equip_count_spins[i].setValue(int(row.get("count", 0)))
                self.equip_rate_spins[i].setValue(float(row.get("hire_rate_day", self.equip_rate_spins[i].value())))
                self.equip_fuel_spins[i].setValue(float(row.get("fuel_lph", self.equip_fuel_spins[i].value())))
                self.equip_util_spins[i].setValue(float(row.get("util_pct", self.equip_util_spins[i].value())))

        # Schedule
        self.days_spin.setValue(int(state.get("days", self.days_spin.value())))
        self.hours_per_day_spin.setValue(float(state.get("hours_per_day", self.hours_per_day_spin.value())))
        self.fuel_price_spin.setValue(float(state.get("fuel_price", self.fuel_price_spin.value())))

        # Overheads
        self.mobilisation_spin.setValue(float(state.get("mobilisation", self.mobilisation_spin.value())))
        self.demobilisation_spin.setValue(float(state.get("demobilisation", self.demobilisation_spin.value())))
        self.daily_plant_overhead_spin.setValue(float(state.get("daily_plant_overhead", self.daily_plant_overhead_spin.value())))
        self.misc_plant_allow_spin.setValue(float(state.get("misc_plant_allow", self.misc_plant_allow_spin.value())))




    def __init__(self, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)

        # Lists of per-row widgets so we can iterate for calculations
        self.equip_name_edits: List[QtWidgets.QLineEdit] = []
        self.equip_count_spins: List[QtWidgets.QSpinBox] = []
        self.equip_rate_spins: List[QtWidgets.QDoubleSpinBox] = []
        self.equip_fuel_spins: List[QtWidgets.QDoubleSpinBox] = []
        self.equip_util_spins: List[QtWidgets.QDoubleSpinBox] = []

        self._build_ui()
        self._connect_signals()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        """
        Build the UI with a scrollable content area.

        Outer layout -> QScrollArea
                     -> inner content widget with all groups.
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

        # ---------------- Equipment list ----------------
        equip_group = QtWidgets.QGroupBox("Equipment and Machinery Fleet", content_widget)
        equip_layout = QtWidgets.QVBoxLayout(equip_group)

        equip_desc = QtWidgets.QLabel(
            "Define your main machines here. Give each item a name (e.g. \"20t Excavator\"), "
            "set the number of units, hire rate per operating hour, fuel consumption and "
            "utilisation (percentage of the working day when it is actually operating). "
            "If an item is not used, set its count or utilisation to 0."
        )
        equip_desc.setWordWrap(True)
        equip_layout.addWidget(equip_desc)

        grid = QtWidgets.QGridLayout()
        grid.setColumnStretch(0, 4)  # name
        grid.setColumnStretch(1, 1)  # count
        grid.setColumnStretch(2, 2)  # rate
        grid.setColumnStretch(3, 2)  # fuel
        grid.setColumnStretch(4, 2)  # utilisation
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(4)

        # Header row
        lbl_name = QtWidgets.QLabel("Equipment name / description")
        lbl_count = QtWidgets.QLabel("Units")
        lbl_rate = QtWidgets.QLabel("Hire rate (USD/h)")
        lbl_fuel = QtWidgets.QLabel("Fuel consumption (L/h)")
        lbl_util = QtWidgets.QLabel("Utilisation (%)")

        for lbl in (lbl_name, lbl_count, lbl_rate, lbl_fuel, lbl_util):
            lbl.setStyleSheet("font-weight: bold;")

        grid.addWidget(lbl_name, 0, 0)
        grid.addWidget(lbl_count, 0, 1)
        grid.addWidget(lbl_rate, 0, 2)
        grid.addWidget(lbl_fuel, 0, 3)
        grid.addWidget(lbl_util, 0, 4)

        # Default row labels for user convenience (these are just examples)
        default_names = [
            "20t Excavator",
            "Wheel Loader",
            "Vibratory Roller",
            "Water Tanker",
            "Concrete Pump",
            "Mobile Crane",
            "Tipper Truck",
            "Telehandler / Forklift",
        ]

        # Reasonable example default rates (purely placeholders)
        default_rates = [90.0, 80.0, 60.0, 55.0, 120.0, 150.0, 70.0, 65.0]
        default_fuel = [18.0, 15.0, 10.0, 8.0, 20.0, 22.0, 14.0, 9.0]

        num_rows = len(default_names)
        for row in range(num_rows):
            name_edit = QtWidgets.QLineEdit(equip_group)
            name_edit.setPlaceholderText("Equipment description")
            name_edit.setText(default_names[row])

            count_spin = QtWidgets.QSpinBox(equip_group)
            count_spin.setRange(0, 1000)
            count_spin.setValue(0)  # default 0 so nothing counts until user sets

            rate_spin = QtWidgets.QDoubleSpinBox(equip_group)
            rate_spin.setSuffix(" $/h")
            rate_spin.setDecimals(2)
            rate_spin.setRange(0.0, 10_000.0)
            rate_spin.setSingleStep(5.0)
            rate_spin.setValue(default_rates[row])

            fuel_spin = QtWidgets.QDoubleSpinBox(equip_group)
            fuel_spin.setSuffix(" L/h")
            fuel_spin.setDecimals(1)
            fuel_spin.setRange(0.0, 1000.0)
            fuel_spin.setSingleStep(0.5)
            fuel_spin.setValue(default_fuel[row])

            util_spin = QtWidgets.QDoubleSpinBox(equip_group)
            util_spin.setSuffix(" %")
            util_spin.setDecimals(1)
            util_spin.setRange(0.0, 100.0)
            util_spin.setSingleStep(5.0)
            util_spin.setValue(70.0)  # default 70% utilisation

            grid.addWidget(name_edit, row + 1, 0)
            grid.addWidget(count_spin, row + 1, 1)
            grid.addWidget(rate_spin, row + 1, 2)
            grid.addWidget(fuel_spin, row + 1, 3)
            grid.addWidget(util_spin, row + 1, 4)

            self.equip_name_edits.append(name_edit)
            self.equip_count_spins.append(count_spin)
            self.equip_rate_spins.append(rate_spin)
            self.equip_fuel_spins.append(fuel_spin)
            self.equip_util_spins.append(util_spin)

        equip_layout.addLayout(grid)

        # ---------------- Global schedule & fuel ----------------
        schedule_group = QtWidgets.QGroupBox("Operating Schedule and Fuel", content_widget)
        schedule_form = QtWidgets.QFormLayout(schedule_group)
        schedule_form.setLabelAlignment(QtCore.Qt.AlignRight)

        # Number of working days
        self.days_spin = QtWidgets.QSpinBox(schedule_group)
        self.days_spin.setRange(1, 3650)
        self.days_spin.setValue(30)

        # Operating hours per day (for each machine's schedule)
        self.hours_per_day_spin = QtWidgets.QDoubleSpinBox(schedule_group)
        self.hours_per_day_spin.setSuffix(" h/day")
        self.hours_per_day_spin.setDecimals(1)
        self.hours_per_day_spin.setRange(0.0, 24.0)
        self.hours_per_day_spin.setSingleStep(0.5)
        self.hours_per_day_spin.setValue(8.0)

        # Fuel price (USD per litre)
        self.fuel_price_spin = QtWidgets.QDoubleSpinBox(schedule_group)
        self.fuel_price_spin.setSuffix(" USD/L")
        self.fuel_price_spin.setDecimals(3)
        self.fuel_price_spin.setRange(0.0, 100.0)
        self.fuel_price_spin.setSingleStep(0.05)
        # Example placeholder, user should override with actual price.
        self.fuel_price_spin.setValue(0.50)

        schedule_form.addRow("Working days:", self.days_spin)
        schedule_form.addRow("Operating hours per day:", self.hours_per_day_spin)
        schedule_form.addRow("Fuel price:", self.fuel_price_spin)

        schedule_note = QtWidgets.QLabel(
            "Each machine's effective hours are based on the global schedule (days × hours/day), "
            "multiplied by its utilisation percentage and number of units. "
            "Fuel cost is calculated from its L/h consumption and the fuel price."
        )
        schedule_note.setWordWrap(True)

        # ---------------- Mobilisation & overheads ----------------
        overhead_group = QtWidgets.QGroupBox("Mobilisation, Plant Overheads and Misc.", content_widget)
        overhead_form = QtWidgets.QFormLayout(overhead_group)
        overhead_form.setLabelAlignment(QtCore.Qt.AlignRight)

        # Mobilisation lump sum (equipment delivery, loading, etc.)
        self.mobilisation_spin = QtWidgets.QDoubleSpinBox(overhead_group)
        self.mobilisation_spin.setSuffix(" USD")
        self.mobilisation_spin.setDecimals(2)
        self.mobilisation_spin.setRange(0.0, 10_000_000.0)
        self.mobilisation_spin.setSingleStep(100.0)
        self.mobilisation_spin.setValue(0.0)

        # Demobilisation lump sum
        self.demobilisation_spin = QtWidgets.QDoubleSpinBox(overhead_group)
        self.demobilisation_spin.setSuffix(" USD")
        self.demobilisation_spin.setDecimals(2)
        self.demobilisation_spin.setRange(0.0, 10_000_000.0)
        self.demobilisation_spin.setSingleStep(100.0)
        self.demobilisation_spin.setValue(0.0)

        # Daily plant overhead (e.g. maintenance, workshop, plant management)
        self.daily_plant_overhead_spin = QtWidgets.QDoubleSpinBox(overhead_group)
        self.daily_plant_overhead_spin.setSuffix(" USD/day")
        self.daily_plant_overhead_spin.setDecimals(2)
        self.daily_plant_overhead_spin.setRange(0.0, 10_000_000.0)
        self.daily_plant_overhead_spin.setSingleStep(50.0)
        self.daily_plant_overhead_spin.setValue(0.0)

        # Misc plant allowance (lump sum)
        self.misc_plant_allow_spin = QtWidgets.QDoubleSpinBox(overhead_group)
        self.misc_plant_allow_spin.setSuffix(" USD")
        self.misc_plant_allow_spin.setDecimals(2)
        self.misc_plant_allow_spin.setRange(0.0, 10_000_000.0)
        self.misc_plant_allow_spin.setSingleStep(100.0)
        self.misc_plant_allow_spin.setValue(0.0)

        overhead_form.addRow("Mobilisation lump sum:", self.mobilisation_spin)
        overhead_form.addRow("Demobilisation lump sum:", self.demobilisation_spin)
        overhead_form.addRow("Daily plant overhead:", self.daily_plant_overhead_spin)
        overhead_form.addRow("Misc plant allowance:", self.misc_plant_allow_spin)

        overhead_note = QtWidgets.QLabel(
            "Mobilisation and demobilisation can cover low-bedding, loading, customs, "
            "and setup. Daily plant overhead can represent workshop, maintenance crew, "
            "standby equipment, and plant management overhead. Misc is a flexible "
            "allowance for small plant-related items and risk."
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

        self.lbl_total_hours = QtWidgets.QLabel("0.0 h", result_group)
        self.lbl_total_hire_cost = QtWidgets.QLabel("$0.00", result_group)
        self.lbl_total_fuel_litres = QtWidgets.QLabel("0.0 L", result_group)
        self.lbl_total_fuel_cost = QtWidgets.QLabel("$0.00", result_group)
        self.lbl_mob_cost = QtWidgets.QLabel("$0.00", result_group)
        self.lbl_overhead_cost = QtWidgets.QLabel("$0.00", result_group)
        self.lbl_grand_total = QtWidgets.QLabel("$0.00", result_group)

        result_form.addRow("Total operating hours (all machines):", self.lbl_total_hours)
        result_form.addRow("Total hire cost:", self.lbl_total_hire_cost)
        result_form.addRow("Total fuel consumption:", self.lbl_total_fuel_litres)
        result_form.addRow("Total fuel cost:", self.lbl_total_fuel_cost)
        result_form.addRow("Mobilisation + demobilisation:", self.lbl_mob_cost)
        result_form.addRow("Plant overhead + misc:", self.lbl_overhead_cost)
        result_form.addRow("Grand total equipment cost:", self.lbl_grand_total)

        # Per-equipment breakdown text area
        self.breakdown_text = QtWidgets.QPlainTextEdit(result_group)
        self.breakdown_text.setReadOnly(True)
        self.breakdown_text.setPlaceholderText(
            "Per-equipment breakdown will appear here after calculation."
        )
        result_form.addRow("Per-equipment breakdown:", self.breakdown_text)

        # ---------------- Assemble content layout ----------------
        content_layout.addWidget(equip_group)
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
    # Core calculation logic
    # ------------------------------------------------------------------

    def _on_calculate_clicked(self) -> None:
        """
        Calculate operating hours, fuel, costs and totals
        for all defined equipment rows.
        """
        days = int(self.days_spin.value())
        hours_per_day = float(self.hours_per_day_spin.value())
        fuel_price = float(self.fuel_price_spin.value())

        mobilisation = float(self.mobilisation_spin.value())
        demobilisation = float(self.demobilisation_spin.value())
        daily_plant_overhead = float(self.daily_plant_overhead_spin.value())
        misc_plant_allow = float(self.misc_plant_allow_spin.value())

        # Basic validation
        if days <= 0:
            QtWidgets.QMessageBox.warning(
                self,
                "Invalid Input",
                "Working days must be greater than zero.",
            )
            return

        if hours_per_day < 0:
            QtWidgets.QMessageBox.warning(
                self,
                "Invalid Input",
                "Operating hours per day cannot be negative.",
            )
            return

        if fuel_price < 0:
            QtWidgets.QMessageBox.warning(
                self,
                "Invalid Input",
                "Fuel price cannot be negative.",
            )
            return

        # Schedule hours available per unit
        schedule_hours = days * hours_per_day

        total_hours = 0.0
        total_hire_cost = 0.0
        total_fuel_litres = 0.0
        total_fuel_cost = 0.0

        breakdown_lines: List[str] = []
        breakdown_lines.append(
            f"Schedule: {days} days × {hours_per_day:.1f} h/day = {schedule_hours:.1f} h per unit (100% utilisation)."
        )
        breakdown_lines.append(
            f"Fuel price: ${fuel_price:.3f} per litre."
        )
        breakdown_lines.append("")
        breakdown_lines.append("Per-equipment details:")
        breakdown_lines.append(
            "Name | Units | Utilisation | Hours | Fuel (L) | Hire cost (USD) | Fuel cost (USD)"
        )
        breakdown_lines.append("-" * 90)

        # Iterate over each equipment row
        num_rows = len(self.equip_name_edits)
        for i in range(num_rows):
            name = self.equip_name_edits[i].text().strip()
            if not name:
                name = f"Item {i + 1}"

            count = int(self.equip_count_spins[i].value())
            rate_hour = float(self.equip_rate_spins[i].value())
            fuel_lph = float(self.equip_fuel_spins[i].value())
            util_pct = float(self.equip_util_spins[i].value())

            # If effectively zero, skip this row
            if count <= 0 or rate_hour <= 0 or util_pct <= 0 or hours_per_day == 0:
                continue

            utilisation_factor = util_pct / 100.0
            hours_effective = count * schedule_hours * utilisation_factor

            hire_cost = hours_effective * rate_hour
            fuel_litres = hours_effective * fuel_lph
            fuel_cost = fuel_litres * fuel_price

            total_hours += hours_effective
            total_hire_cost += hire_cost
            total_fuel_litres += fuel_litres
            total_fuel_cost += fuel_cost

            breakdown_lines.append(
                f"{name} | {count} | {util_pct:.1f}% | "
                f"{hours_effective:,.1f} h | {fuel_litres:,.1f} L | "
                f"${hire_cost:,.2f} | ${fuel_cost:,.2f}"
            )

        # Overheads & mobilisation
        mob_cost = mobilisation + demobilisation
        overhead_cost = daily_plant_overhead * days + misc_plant_allow

        grand_total = total_hire_cost + total_fuel_cost + mob_cost + overhead_cost

        # Update result labels
        self.lbl_total_hours.setText(f"{total_hours:,.1f} h")
        self.lbl_total_hire_cost.setText(f"${total_hire_cost:,.2f}")
        self.lbl_total_fuel_litres.setText(f"{total_fuel_litres:,.1f} L")
        self.lbl_total_fuel_cost.setText(f"${total_fuel_cost:,.2f}")
        self.lbl_mob_cost.setText(f"${mob_cost:,.2f}")
        self.lbl_overhead_cost.setText(f"${overhead_cost:,.2f}")
        self.lbl_grand_total.setText(f"${grand_total:,.2f}")

        breakdown_lines.append("")
        breakdown_lines.append(f"Total operating hours (all machines): {total_hours:,.1f} h")
        breakdown_lines.append(f"Total hire cost: ${total_hire_cost:,.2f}")
        breakdown_lines.append(f"Total fuel consumption: {total_fuel_litres:,.1f} L")
        breakdown_lines.append(f"Total fuel cost: ${total_fuel_cost:,.2f}")
        breakdown_lines.append(f"Mobilisation + demobilisation: ${mob_cost:,.2f}")
        breakdown_lines.append(f"Plant overhead + misc: ${overhead_cost:,.2f}")
        breakdown_lines.append(f"Grand total equipment cost: ${grand_total:,.2f}")

        self.breakdown_text.setPlainText("\n".join(breakdown_lines))

    def _on_reset_clicked(self) -> None:
        """Reset all inputs and outputs to default values."""
        # Reset equipment rows: counts and utilisation to 0, keep default rates & names
        for i in range(len(self.equip_name_edits)):
            self.equip_count_spins[i].setValue(0)
            self.equip_util_spins[i].setValue(70.0)

        # Schedule
        self.days_spin.setValue(30)
        self.hours_per_day_spin.setValue(8.0)
        self.fuel_price_spin.setValue(0.50)

        # Overheads
        self.mobilisation_spin.setValue(0.0)
        self.demobilisation_spin.setValue(0.0)
        self.daily_plant_overhead_spin.setValue(0.0)
        self.misc_plant_allow_spin.setValue(0.0)

        # Results
        self.lbl_total_hours.setText("0.0 h")
        self.lbl_total_hire_cost.setText("$0.00")
        self.lbl_total_fuel_litres.setText("0.0 L")
        self.lbl_total_fuel_cost.setText("$0.00")
        self.lbl_mob_cost.setText("$0.00")
        self.lbl_overhead_cost.setText("$0.00")
        self.lbl_grand_total.setText("$0.00")
        self.breakdown_text.clear()
        self.breakdown_text.setPlaceholderText(
            "Per-equipment breakdown will appear here after calculation."
        )
