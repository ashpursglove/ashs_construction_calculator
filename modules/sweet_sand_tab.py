
"""
sweet_sand_tab.py

PyQt5 widget implementing a sweet sand calculator for filling a
racetrack-shaped reactor base to a specified height, including
a corner radius (sand fillet) along:
- the external perimeter (floor-to-outer-wall), and
- both sides of a central divider wall that spans the straight section.

It also estimates total material cost in USD from a user-specified
cost per metric tonne.

Geometry
--------
The reactor base plan is assumed to be:
- A central rectangle of length L_rect and width W,
- With semicircular ends of radius R = W/2.

User inputs:
- L_total      : overall reactor length (including both semicircular ends) [m]
- W            : internal width (also the diameter of each arc) [m]
- H_cm         : fill height (depth of sweet sand) [cm]
- r_corner_cm  : corner radius for the sand fillet at the floor-to-wall corner [cm]
- rho          : bulk density of sweet sand [kg/m³]
- cost_per_ton : cost of sweet sand per metric tonne [USD/t]

Derived:
    L_rect = L_total - W          (straight middle section length)
    R      = W / 2
    Area   = W * L_rect + π * R²  (plan area of base, m²)

Base fill volume (flat base only):
    H      = H_cm / 100           (convert cm → m)
    V_base = Area * H

Corner radius fillets:
- Modelled as a quarter-circular fillet with radius r_corner (m)
  running along:
    * the full external perimeter
    * both sides of the central divider wall (length L_rect each side)

Perimeter of racetrack shape (outer walls):
    P_outer = 2 * L_rect + 2 * π * R

Central wall (both sides):
    P_center = 2 * L_rect

Total fillet length:
    P_total = P_outer + P_center = 4 * L_rect + 2 * π * R

Cross-section area of quarter-circle:
    A_fillet = π * r_corner² / 4

Fillet volume:
    V_fillet = P_total * A_fillet

Total volume:
    V_total = V_base + V_fillet

Weight:
    weight_kg   = V_total * rho
    weight_tons = weight_kg / 1000

Cost:
    total_cost  = weight_tons * cost_per_ton
"""

import math
from typing import Optional

from PyQt5 import QtCore, QtWidgets


class SweetSandTab(QtWidgets.QWidget):
    """
    Main widget for the sweet sand calculator tab.
    Designed to be dropped into a QTabWidget.
    """



    # ------------------------------------------------------------------
    # Project Save/Load
    # ------------------------------------------------------------------

    def export_state(self) -> dict:
        return {
            "length_total": float(self.length_total_spin.value()),
            "width": float(self.width_spin.value()),
            "fill_height": float(self.fill_height_spin.value()),
            "corner_radius": float(self.corner_radius_spin.value()),
            "bulk_density": float(self.bulk_density_spin.value()),
            "cost_per_ton": float(self.cost_per_ton_spin.value()),
        }

    def import_state(self, state: dict) -> None:
        if not isinstance(state, dict):
            return

        self.length_total_spin.setValue(float(state.get("length_total", 0.0)))
        self.width_spin.setValue(float(state.get("width", 0.0)))
        self.fill_height_spin.setValue(float(state.get("fill_height", 0.0)))
        self.corner_radius_spin.setValue(float(state.get("corner_radius", 0.0)))
        self.bulk_density_spin.setValue(float(state.get("bulk_density", self.bulk_density_spin.value())))
        self.cost_per_ton_spin.setValue(float(state.get("cost_per_ton", self.cost_per_ton_spin.value())))


    def __init__(self, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        self._build_ui()
        self._connect_signals()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        """Create all widgets and layouts."""

        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(10)

        # ---------------- Reactor Geometry ----------------
        geom_group = QtWidgets.QGroupBox("Reactor Geometry", self)
        geom_form = QtWidgets.QFormLayout(geom_group)
        geom_form.setLabelAlignment(QtCore.Qt.AlignRight)

        # Overall length (including both semicircular ends)
        self.length_total_spin = QtWidgets.QDoubleSpinBox(geom_group)
        self.length_total_spin.setSuffix(" m")
        self.length_total_spin.setDecimals(3)
        self.length_total_spin.setRange(0.0, 10000.0)
        self.length_total_spin.setSingleStep(0.1)

        # Internal width (also the diameter of each arc)
        self.width_spin = QtWidgets.QDoubleSpinBox(geom_group)
        self.width_spin.setSuffix(" m")
        self.width_spin.setDecimals(3)
        self.width_spin.setRange(0.0, 10000.0)
        self.width_spin.setSingleStep(0.1)

        # Fill height (depth of sweet sand) - entered in centimeters
        self.fill_height_spin = QtWidgets.QDoubleSpinBox(geom_group)
        self.fill_height_spin.setSuffix(" cm")
        self.fill_height_spin.setDecimals(1)
        self.fill_height_spin.setRange(0.0, 500.0)   # up to 5 m depth if needed
        self.fill_height_spin.setSingleStep(1.0)

        # Corner radius for sand fillet at floor-to-wall junction (cm)
        self.corner_radius_spin = QtWidgets.QDoubleSpinBox(geom_group)
        self.corner_radius_spin.setSuffix(" cm")
        self.corner_radius_spin.setDecimals(1)
        self.corner_radius_spin.setRange(0.0, 200.0)  # up to 2 m radius
        self.corner_radius_spin.setSingleStep(1.0)

        geom_form.addRow("Overall reactor length (L):", self.length_total_spin)
        geom_form.addRow("Internal width / arc diameter (W):", self.width_spin)
        geom_form.addRow("Fill height (H):", self.fill_height_spin)
        geom_form.addRow("Corner radius (floor-to-wall):", self.corner_radius_spin)

        # Helpful note
        note_label = QtWidgets.QLabel(
            "Note: L is the total inside length including both semicircular ends.\n"
            "The short ends are arcs with diameter equal to the reactor width.\n"
            "A central wall spans the straight section (length L - W) with fillets on both sides.\n"
            "Corner radius is treated as a quarter-circular fillet along all floor-to-wall junctions."
        )
        note_label.setWordWrap(True)

        # ---------------- Material Properties ----------------
        material_group = QtWidgets.QGroupBox("Material Properties (Sweet Sand)", self)
        material_form = QtWidgets.QFormLayout(material_group)
        material_form.setLabelAlignment(QtCore.Qt.AlignRight)

        # Bulk density (kg/m³)
        self.bulk_density_spin = QtWidgets.QDoubleSpinBox(material_group)
        self.bulk_density_spin.setSuffix(" kg/m³")
        self.bulk_density_spin.setDecimals(1)
        self.bulk_density_spin.setRange(0.0, 5000.0)
        self.bulk_density_spin.setSingleStep(10.0)
        # Typical dry sand bulk density ~1600 kg/m³
        self.bulk_density_spin.setValue(1600.0)

        # Cost per metric tonne (USD/t)
        self.cost_per_ton_spin = QtWidgets.QDoubleSpinBox(material_group)
        self.cost_per_ton_spin.setSuffix(" USD/t")
        self.cost_per_ton_spin.setDecimals(2)
        self.cost_per_ton_spin.setRange(0.0, 1000.0)
        self.cost_per_ton_spin.setSingleStep(1.0)
        # Default based on ~80 SAR/m³ soft white sand and 1600 kg/m³ density:
        # 80 SAR/m³ ≈ 50 SAR/t, 1 USD ≈ 3.75 SAR ⇒ ~13.3 USD/t.
        self.cost_per_ton_spin.setValue(13.3)

        material_form.addRow("Bulk density:", self.bulk_density_spin)
        material_form.addRow("Cost per tonne:", self.cost_per_ton_spin)

        # ---------------- Buttons ----------------
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addStretch(1)

        self.reset_button = QtWidgets.QPushButton("Reset", self)
        self.reset_button.setObjectName("secondaryButton")

        self.calculate_button = QtWidgets.QPushButton("Calculate", self)
        self.calculate_button.setObjectName("primaryButton")

        button_layout.addWidget(self.reset_button)
        button_layout.addWidget(self.calculate_button)

        # ---------------- Results ----------------
        result_group = QtWidgets.QGroupBox("Results", self)
        result_form = QtWidgets.QFormLayout(result_group)
        result_form.setLabelAlignment(QtCore.Qt.AlignRight)

        self.lbl_rect_length = QtWidgets.QLabel("0.000 m", result_group)
        self.lbl_radius = QtWidgets.QLabel("0.000 m", result_group)
        self.lbl_plan_area = QtWidgets.QLabel("0.00 m²", result_group)
        self.lbl_volume_base = QtWidgets.QLabel("0.000 m³", result_group)
        self.lbl_volume_corner = QtWidgets.QLabel("0.000 m³", result_group)
        self.lbl_volume_total = QtWidgets.QLabel("0.000 m³", result_group)
        self.lbl_weight_kg = QtWidgets.QLabel("0 kg", result_group)
        self.lbl_weight_tons = QtWidgets.QLabel("0.000 t", result_group)
        self.lbl_total_cost = QtWidgets.QLabel("$0.00", result_group)

        result_form.addRow("Straight section length (L - W):", self.lbl_rect_length)
        result_form.addRow("Arc radius (W / 2):", self.lbl_radius)
        result_form.addRow("Plan area:", self.lbl_plan_area)
        result_form.addRow("Base fill volume:", self.lbl_volume_base)
        result_form.addRow("Corner radius volume:", self.lbl_volume_corner)
        result_form.addRow("Total volume:", self.lbl_volume_total)
        result_form.addRow("Weight:", self.lbl_weight_kg)
        result_form.addRow("Weight (metric tons):", self.lbl_weight_tons)
        result_form.addRow("Total material cost:", self.lbl_total_cost)

        # ---------------- Assemble layout ----------------
        main_layout.addWidget(geom_group)
        main_layout.addWidget(note_label)
        main_layout.addWidget(material_group)
        main_layout.addLayout(button_layout)
        main_layout.addWidget(result_group)
        main_layout.addStretch(1)

    # ------------------------------------------------------------------
    # Signal wiring
    # ------------------------------------------------------------------

    def _connect_signals(self) -> None:
        """Connect signals to slots."""
        self.calculate_button.clicked.connect(self._on_calculate_clicked)
        self.reset_button.clicked.connect(self._on_reset_clicked)

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    def _on_calculate_clicked(self) -> None:
        """
        Compute the required volume and weight of sweet sand
        to fill the reactor base to the specified height, including
        corner radius fillets along the external walls and both
        sides of the central divider, and estimate total cost.
        """

        L_total = float(self.length_total_spin.value())
        W = float(self.width_spin.value())
        H_cm = float(self.fill_height_spin.value())
        r_corner_cm = float(self.corner_radius_spin.value())
        rho = float(self.bulk_density_spin.value())
        cost_per_ton = float(self.cost_per_ton_spin.value())

        # Convert cm inputs to meters
        H = H_cm / 100.0
        r_corner = r_corner_cm / 100.0

        # Basic validation of geometry & materials
        if L_total <= 0 or W <= 0 or H <= 0 or rho <= 0 or cost_per_ton < 0:
            QtWidgets.QMessageBox.warning(
                self,
                "Invalid Input",
                "Please ensure length, width, height and density are all > 0,\n"
                "and cost per tonne is not negative.",
            )
            return

        if L_total <= W:
            QtWidgets.QMessageBox.warning(
                self,
                "Geometry Warning",
                "Overall length (L) must be greater than width (W)\n"
                "so that a straight section exists between the arcs.\n"
                "Currently, L <= W. Please adjust the dimensions.",
            )
            return

        # Geometry
        L_rect = L_total - W
        R = W / 2.0

        # Plan area: rectangle + full circle (two semicircles)
        area_rect = W * L_rect
        area_circle = math.pi * (R ** 2)
        area_total = area_rect + area_circle

        # Base fill volume (flat base)
        volume_base = area_total * H  # m³

        # Corner radius fillet volume (optional if r_corner > 0)
        if r_corner > 0.0:
            # External racetrack perimeter
            perimeter_outer = 2.0 * L_rect + 2.0 * math.pi * R
            # Central wall, both sides
            perimeter_center = 2.0 * L_rect
            # Total fillet run length
            perimeter_total = perimeter_outer + perimeter_center

            # Quarter-circle cross-section area
            fillet_cross_section = math.pi * (r_corner ** 2) / 4.0
            volume_corner = perimeter_total * fillet_cross_section
        else:
            volume_corner = 0.0

        # Total volume and weight
        volume_total = volume_base + volume_corner
        weight_kg = volume_total * rho
        weight_tons = weight_kg / 1000.0

        # Cost
        total_cost = weight_tons * cost_per_ton

        # Update labels
        self.lbl_rect_length.setText(f"{L_rect:,.3f} m")
        self.lbl_radius.setText(f"{R:,.3f} m")
        self.lbl_plan_area.setText(f"{area_total:,.2f} m²")
        self.lbl_volume_base.setText(f"{volume_base:,.3f} m³")
        self.lbl_volume_corner.setText(f"{volume_corner:,.3f} m³")
        self.lbl_volume_total.setText(f"{volume_total:,.3f} m³")
        self.lbl_weight_kg.setText(f"{weight_kg:,.0f} kg")
        self.lbl_weight_tons.setText(f"{weight_tons:,.3f} t")
        self.lbl_total_cost.setText(f"${total_cost:,.2f}")

    def _on_reset_clicked(self) -> None:
        """Reset all inputs and results to defaults."""
        self.length_total_spin.setValue(0.0)
        self.width_spin.setValue(0.0)
        self.fill_height_spin.setValue(0.0)
        self.corner_radius_spin.setValue(0.0)

        # Reset density and cost defaults
        self.bulk_density_spin.setValue(1600.0)
        self.cost_per_ton_spin.setValue(13.3)

        self.lbl_rect_length.setText("0.000 m")
        self.lbl_radius.setText("0.000 m")
        self.lbl_plan_area.setText("0.00 m²")
        self.lbl_volume_base.setText("0.000 m³")
        self.lbl_volume_corner.setText("0.000 m³")
        self.lbl_volume_total.setText("0.000 m³")
        self.lbl_weight_kg.setText("0 kg")
        self.lbl_weight_tons.setText("0.000 t")
        self.lbl_total_cost.setText("$0.00")






