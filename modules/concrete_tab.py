
"""
concrete_tab.py

PyQt5 widget implementing a concrete works calculator for common
elements:
- Slab / base
- Strip footing
- Wall
- Isolated footing

For each element type, the tab estimates:
- Concrete volume (m³)
- Concrete weight (kg)
- Approximate vertical formwork area (m²)
- Rebar weight (kg and tonnes) using a specified kg/m³ intensity
- Material cost for concrete and rebar (USD)
- Total material cost (USD)

It also shows a short description of the selected element type so that
non-specialists can understand what "slab/base", "strip footing", etc.
refer to.

Assumptions & Defaults
----------------------
- Concrete density default: 2400 kg/m³
- Concrete cost default: ~60 USD/m³
- Rebar intensity default: 100 kg/m³, typical for reinforced
  building elements.
- Rebar cost default: ~640 USD/t

Geometry models (per element)
-----------------------------
All dimensions are in meters unless noted.

1) Slab / Base
    Inputs:
        - Length L (m)
        - Width W (m)
        - Thickness T_cm (cm → T = T_cm/100)
        - Count N

    Volume:
        V = L * W * T * N

    Approx vertical formwork area:
        A_form = perimeter * T * N
               = 2*(L+W) * T * N
        (Assumes all four edges are formed.)

2) Strip Footing
    Inputs:
        - Total footing length L (m)
        - Width W (m)
        - Thickness T_cm (cm → T = T_cm/100)

    Volume:
        V = L * W * T

    Approx vertical formwork area:
        A_form ≈ 2 * L * T
        (Assumes strips cast in a trench; side faces only.)

3) Wall
    Inputs:
        - Length L (m)
        - Height H (m)
        - Thickness T_cm (cm → T = T_cm/100)
        - Count N

    Volume:
        V = L * H * T * N

    Approx formwork area:
        A_form = 2 * L * H * N
        (Both faces formed; end faces ignored.)

4) Isolated Footing
    Inputs:
        - Footing length L (m)
        - Footing width W (m)
        - Thickness T_cm (cm → T = T_cm/100)
        - Count N

    Volume:
        V = L * W * T * N

    Approx vertical formwork area:
        A_form = 2*(L + W) * T * N
        (Four vertical sides formed.)
"""

from typing import Optional

from PyQt5 import QtCore, QtWidgets


class ConcreteTab(QtWidgets.QWidget):
    """
    Main widget for the concrete works calculator tab.
    Designed to be dropped into a QTabWidget.
    """



    # ------------------------------------------------------------------
    # Project Save/Load
    # ------------------------------------------------------------------


    def export_state(self) -> dict:
        return {
            "element_type_index": int(self.element_type_combo.currentIndex()),

            # Slab / base
            "slab_length": float(self.slab_length_spin.value()),
            "slab_width": float(self.slab_width_spin.value()),
            "slab_thickness_cm": float(self.slab_thickness_spin.value()),
            "slab_count": int(self.slab_count_spin.value()),

            # Strip footing
            "strip_length": float(self.strip_length_spin.value()),
            "strip_width": float(self.strip_width_spin.value()),
            "strip_thickness_cm": float(self.strip_thickness_spin.value()),

            # Wall
            "wall_length": float(self.wall_length_spin.value()),
            "wall_height": float(self.wall_height_spin.value()),
            "wall_thickness_cm": float(self.wall_thickness_spin.value()),
            "wall_count": int(self.wall_count_spin.value()),

            # Isolated footing (iso_* is correct)
            "iso_length": float(self.iso_length_spin.value()),
            "iso_width": float(self.iso_width_spin.value()),
            "iso_thickness_cm": float(self.iso_thickness_spin.value()),
            "iso_count": int(self.iso_count_spin.value()),

            # Materials
            "conc_density": float(self.conc_density_spin.value()),
            "conc_cost": float(self.conc_cost_spin.value()),
            "rebar_intensity": float(self.rebar_intensity_spin.value()),
            "rebar_cost": float(self.rebar_cost_spin.value()),
        }



    def import_state(self, state: dict) -> None:
        if not isinstance(state, dict):
            return

        idx = int(state.get("element_type_index", self.element_type_combo.currentIndex()))
        if 0 <= idx < self.element_type_combo.count():
            self.element_type_combo.setCurrentIndex(idx)

        # Slab
        self.slab_length_spin.setValue(float(state.get("slab_length", 0.0)))
        self.slab_width_spin.setValue(float(state.get("slab_width", 0.0)))
        self.slab_thickness_spin.setValue(float(state.get("slab_thickness_cm", 0.0)))
        self.slab_count_spin.setValue(int(state.get("slab_count", 1)))

        # Strip footing
        self.strip_length_spin.setValue(float(state.get("strip_length", 0.0)))
        self.strip_width_spin.setValue(float(state.get("strip_width", 0.0)))
        self.strip_thickness_spin.setValue(float(state.get("strip_thickness_cm", 0.0)))

        # Wall
        self.wall_length_spin.setValue(float(state.get("wall_length", 0.0)))
        self.wall_height_spin.setValue(float(state.get("wall_height", 0.0)))
        self.wall_thickness_spin.setValue(float(state.get("wall_thickness_cm", 0.0)))
        self.wall_count_spin.setValue(int(state.get("wall_count", 1)))

        # Isolated footing
        self.iso_length_spin.setValue(float(state.get("iso_length", 0.0)))
        self.iso_width_spin.setValue(float(state.get("iso_width", 0.0)))
        self.iso_thickness_spin.setValue(float(state.get("iso_thickness_cm", 0.0)))
        self.iso_count_spin.setValue(int(state.get("iso_count", 1)))

        # Materials
        self.conc_density_spin.setValue(float(state.get("conc_density", self.conc_density_spin.value())))
        self.conc_cost_spin.setValue(float(state.get("conc_cost", self.conc_cost_spin.value())))
        self.rebar_intensity_spin.setValue(float(state.get("rebar_intensity", self.rebar_intensity_spin.value())))
        self.rebar_cost_spin.setValue(float(state.get("rebar_cost", self.rebar_cost_spin.value())))


    def __init__(self, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        self._build_ui()
        self._connect_signals()
        # Initialise element description for the default selection
        self._update_element_description(self.element_type_combo.currentIndex())

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        """Create all widgets and layouts."""

        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(10)

        # ---------------- Element selection & geometry ----------------
        geom_group = QtWidgets.QGroupBox("Element Type and Geometry", self)
        geom_layout = QtWidgets.QVBoxLayout(geom_group)

        # Element type selector
        type_layout = QtWidgets.QHBoxLayout()
        type_layout.addWidget(QtWidgets.QLabel("Element type:"))
        self.element_type_combo = QtWidgets.QComboBox(geom_group)
        self.element_type_combo.addItems(
            [
                "Slab / Base",
                "Strip Footing",
                "Wall",
                "Isolated Footing",
            ]
        )
        type_layout.addWidget(self.element_type_combo)
        type_layout.addStretch(1)

        geom_layout.addLayout(type_layout)

        # Description label for selected element type
        self.element_description_label = QtWidgets.QLabel(geom_group)
        self.element_description_label.setWordWrap(True)
        self.element_description_label.setStyleSheet(
            "color: #A9B0C5; font-size: 11px;"
        )
        geom_layout.addWidget(self.element_description_label)

        # Stacked widget for element-specific geometry inputs
        self.geom_stack = QtWidgets.QStackedWidget(geom_group)

        # --- Slab / Base geometry widget ---
        self.slab_widget = QtWidgets.QWidget(geom_group)
        slab_form = QtWidgets.QFormLayout(self.slab_widget)
        slab_form.setLabelAlignment(QtCore.Qt.AlignRight)

        self.slab_length_spin = QtWidgets.QDoubleSpinBox(self.slab_widget)
        self._setup_length_width(self.slab_length_spin)

        self.slab_width_spin = QtWidgets.QDoubleSpinBox(self.slab_widget)
        self._setup_length_width(self.slab_width_spin)

        self.slab_thickness_spin = QtWidgets.QDoubleSpinBox(self.slab_widget)
        self._setup_thickness_cm(self.slab_thickness_spin)

        self.slab_count_spin = QtWidgets.QSpinBox(self.slab_widget)
        self.slab_count_spin.setRange(1, 9999)
        self.slab_count_spin.setValue(1)

        slab_form.addRow("Length L (m):", self.slab_length_spin)
        slab_form.addRow("Width W (m):", self.slab_width_spin)
        slab_form.addRow("Thickness T (cm):", self.slab_thickness_spin)
        slab_form.addRow("Number of slabs:", self.slab_count_spin)

        # --- Strip Footing geometry widget ---
        self.footing_strip_widget = QtWidgets.QWidget(geom_group)
        strip_form = QtWidgets.QFormLayout(self.footing_strip_widget)
        strip_form.setLabelAlignment(QtCore.Qt.AlignRight)

        self.strip_length_spin = QtWidgets.QDoubleSpinBox(self.footing_strip_widget)
        self._setup_length_width(self.strip_length_spin)
        self.strip_length_spin.setToolTip("Total length of all strip footings (m).")

        self.strip_width_spin = QtWidgets.QDoubleSpinBox(self.footing_strip_widget)
        self._setup_length_width(self.strip_width_spin)

        self.strip_thickness_spin = QtWidgets.QDoubleSpinBox(self.footing_strip_widget)
        self._setup_thickness_cm(self.strip_thickness_spin)

        strip_form.addRow("Total footing length L (m):", self.strip_length_spin)
        strip_form.addRow("Footing width W (m):", self.strip_width_spin)
        strip_form.addRow("Footing thickness T (cm):", self.strip_thickness_spin)

        # --- Wall geometry widget ---
        self.wall_widget = QtWidgets.QWidget(geom_group)
        wall_form = QtWidgets.QFormLayout(self.wall_widget)
        wall_form.setLabelAlignment(QtCore.Qt.AlignRight)

        self.wall_length_spin = QtWidgets.QDoubleSpinBox(self.wall_widget)
        self._setup_length_width(self.wall_length_spin)

        self.wall_height_spin = QtWidgets.QDoubleSpinBox(self.wall_widget)
        self.wall_height_spin.setSuffix(" m")
        self.wall_height_spin.setDecimals(3)
        self.wall_height_spin.setRange(0.0, 100.0)
        self.wall_height_spin.setSingleStep(0.1)

        self.wall_thickness_spin = QtWidgets.QDoubleSpinBox(self.wall_widget)
        self._setup_thickness_cm(self.wall_thickness_spin)

        self.wall_count_spin = QtWidgets.QSpinBox(self.wall_widget)
        self.wall_count_spin.setRange(1, 9999)
        self.wall_count_spin.setValue(1)

        wall_form.addRow("Wall length L (m):", self.wall_length_spin)
        wall_form.addRow("Wall height H (m):", self.wall_height_spin)
        wall_form.addRow("Wall thickness T (cm):", self.wall_thickness_spin)
        wall_form.addRow("Number of walls:", self.wall_count_spin)

        # --- Isolated Footing geometry widget ---
        self.footing_iso_widget = QtWidgets.QWidget(geom_group)
        iso_form = QtWidgets.QFormLayout(self.footing_iso_widget)
        iso_form.setLabelAlignment(QtCore.Qt.AlignRight)

        self.iso_length_spin = QtWidgets.QDoubleSpinBox(self.footing_iso_widget)
        self._setup_length_width(self.iso_length_spin)

        self.iso_width_spin = QtWidgets.QDoubleSpinBox(self.footing_iso_widget)
        self._setup_length_width(self.iso_width_spin)

        self.iso_thickness_spin = QtWidgets.QDoubleSpinBox(self.footing_iso_widget)
        self._setup_thickness_cm(self.iso_thickness_spin)

        self.iso_count_spin = QtWidgets.QSpinBox(self.footing_iso_widget)
        self.iso_count_spin.setRange(1, 9999)
        self.iso_count_spin.setValue(1)

        iso_form.addRow("Footing length L (m):", self.iso_length_spin)
        iso_form.addRow("Footing width W (m):", self.iso_width_spin)
        iso_form.addRow("Footing thickness T (cm):", self.iso_thickness_spin)
        iso_form.addRow("Number of footings:", self.iso_count_spin)

        # Add each geometry widget to stacked widget
        self.geom_stack.addWidget(self.slab_widget)           # index 0
        self.geom_stack.addWidget(self.footing_strip_widget)  # index 1
        self.geom_stack.addWidget(self.wall_widget)           # index 2
        self.geom_stack.addWidget(self.footing_iso_widget)    # index 3

        geom_layout.addWidget(self.geom_stack)

        # Helpful note (general)
        note_label = QtWidgets.QLabel(
            "Note: This tab provides approximate quantities for concrete, rebar and formwork.\n"
            "Always cross-check with structural design drawings and local codes."
        )
        note_label.setWordWrap(True)

        # ---------------- Material & cost properties ----------------
        material_group = QtWidgets.QGroupBox("Material Properties and Costs", self)
        material_form = QtWidgets.QFormLayout(material_group)
        material_form.setLabelAlignment(QtCore.Qt.AlignRight)

        # Concrete density
        self.conc_density_spin = QtWidgets.QDoubleSpinBox(material_group)
        self.conc_density_spin.setSuffix(" kg/m³")
        self.conc_density_spin.setDecimals(1)
        self.conc_density_spin.setRange(0.0, 5000.0)
        self.conc_density_spin.setSingleStep(10.0)
        self.conc_density_spin.setValue(2400.0)

        # Concrete cost per m³ (USD)
        self.conc_cost_spin = QtWidgets.QDoubleSpinBox(material_group)
        self.conc_cost_spin.setSuffix(" USD/m³")
        self.conc_cost_spin.setDecimals(2)
        self.conc_cost_spin.setRange(0.0, 1000.0)
        self.conc_cost_spin.setSingleStep(5.0)
        # Example: ~200–225 SAR/m³ at SAR≈3.75 / USD ⇒ around 55–60 USD/m³
        self.conc_cost_spin.setValue(60.0)

        # Rebar intensity (kg/m³)
        self.rebar_intensity_spin = QtWidgets.QDoubleSpinBox(material_group)
        self.rebar_intensity_spin.setSuffix(" kg/m³")
        self.rebar_intensity_spin.setDecimals(1)
        self.rebar_intensity_spin.setRange(0.0, 500.0)
        self.rebar_intensity_spin.setSingleStep(5.0)
        self.rebar_intensity_spin.setValue(100.0)

        # Quick selector for typical rebar intensities
        self.rebar_level_combo = QtWidgets.QComboBox(material_group)
        self.rebar_level_combo.addItems(
            [
                "Custom",
                "Light (60 kg/m³)",
                "Medium (90 kg/m³)",
                "Heavy (120 kg/m³)",
            ]
        )
        self.rebar_level_combo.setCurrentIndex(0)

        # Rebar cost per tonne (USD/t)
        self.rebar_cost_spin = QtWidgets.QDoubleSpinBox(material_group)
        self.rebar_cost_spin.setSuffix(" USD/t")
        self.rebar_cost_spin.setDecimals(2)
        self.rebar_cost_spin.setRange(0.0, 2000.0)
        self.rebar_cost_spin.setSingleStep(10.0)
        # Example: ~2400 SAR/t ≈ 640 USD/t
        self.rebar_cost_spin.setValue(640.0)

        material_form.addRow("Concrete density:", self.conc_density_spin)
        material_form.addRow("Concrete cost:", self.conc_cost_spin)
        material_form.addRow("Rebar intensity:", self.rebar_intensity_spin)
        material_form.addRow("Rebar intensity preset:", self.rebar_level_combo)
        material_form.addRow("Rebar cost:", self.rebar_cost_spin)

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

        self.lbl_volume = QtWidgets.QLabel("0.000 m³", result_group)
        self.lbl_conc_weight = QtWidgets.QLabel("0 kg", result_group)
        self.lbl_form_area = QtWidgets.QLabel("0.00 m²", result_group)
        self.lbl_rebar_kg = QtWidgets.QLabel("0 kg", result_group)
        self.lbl_rebar_tons = QtWidgets.QLabel("0.000 t", result_group)
        self.lbl_conc_cost = QtWidgets.QLabel("$0.00", result_group)
        self.lbl_rebar_cost = QtWidgets.QLabel("$0.00", result_group)
        self.lbl_total_cost = QtWidgets.QLabel("$0.00", result_group)

        result_form.addRow("Concrete volume:", self.lbl_volume)
        result_form.addRow("Concrete weight:", self.lbl_conc_weight)
        result_form.addRow("Formwork area (vertical):", self.lbl_form_area)
        result_form.addRow("Rebar quantity:", self.lbl_rebar_kg)
        result_form.addRow("Rebar quantity (t):", self.lbl_rebar_tons)
        result_form.addRow("Concrete cost:", self.lbl_conc_cost)
        result_form.addRow("Rebar cost:", self.lbl_rebar_cost)
        result_form.addRow("Total material cost:", self.lbl_total_cost)

        # ---------------- Assemble layout ----------------
        main_layout.addWidget(geom_group)
        main_layout.addWidget(note_label)
        main_layout.addWidget(material_group)
        main_layout.addLayout(button_layout)
        main_layout.addWidget(result_group)
        main_layout.addStretch(1)

    # ------------------------------------------------------------------
    # Helper configuration for spin boxes
    # ------------------------------------------------------------------

    @staticmethod
    def _setup_length_width(spin: QtWidgets.QDoubleSpinBox) -> None:
        """Configure a spin box for length/width in meters."""
        spin.setSuffix(" m")
        spin.setDecimals(3)
        spin.setRange(0.0, 10000.0)
        spin.setSingleStep(0.1)

    @staticmethod
    def _setup_thickness_cm(spin: QtWidgets.QDoubleSpinBox) -> None:
        """Configure a spin box for thickness in centimeters."""
        spin.setSuffix(" cm")
        spin.setDecimals(1)
        spin.setRange(0.0, 500.0)  # up to 5 m thick if needed
        spin.setSingleStep(1.0)

    # ------------------------------------------------------------------
    # Signal wiring
    # ------------------------------------------------------------------

    def _connect_signals(self) -> None:
        """Connect signals to slots."""
        self.element_type_combo.currentIndexChanged.connect(
            self._on_element_type_changed
        )
        self.rebar_level_combo.currentIndexChanged.connect(
            self._on_rebar_level_changed
        )
        self.calculate_button.clicked.connect(self._on_calculate_clicked)
        self.reset_button.clicked.connect(self._on_reset_clicked)

    # ------------------------------------------------------------------
    # Element description logic
    # ------------------------------------------------------------------

    def _update_element_description(self, index: int) -> None:
        """
        Update the text under the element selector to explain
        what the currently selected element type represents.
        """
        if index == 0:
            # Slab / Base
            text = (
                "Slab / Base: A flat, horizontal concrete element such as a floor slab, "
                "equipment pad or raft base. Defined by length, width and thickness, "
                "with one or more identical slabs."
            )
        elif index == 1:
            # Strip footing
            text = (
                "Strip Footing: A continuous strip of concrete running under walls or rows of columns. "
                "Defined by total strip length, width and thickness. Often cast in a trench."
            )
        elif index == 2:
            # Wall
            text = (
                "Wall: A vertical reinforced concrete wall, such as a retaining wall or tank wall. "
                "Defined by length, clear height and thickness, with an optional count of identical walls."
            )
        elif index == 3:
            # Isolated footing
            text = (
                "Isolated Footing: A single pad footing under a column or small group of columns. "
                "Defined by plan length, plan width and thickness, with a count for multiple footings."
            )
        else:
            text = ""

        self.element_description_label.setText(text)

    # ------------------------------------------------------------------
    # Slots and core logic
    # ------------------------------------------------------------------

    def _on_element_type_changed(self, index: int) -> None:
        """Switch visible geometry input form based on element type."""
        self.geom_stack.setCurrentIndex(index)
        self._update_element_description(index)

    def _on_rebar_level_changed(self, index: int) -> None:
        """
        Apply preset rebar intensities when a level is selected.
        Index 0 = Custom, do nothing.
        """
        if index == 1:      # Light
            value = 60.0
        elif index == 2:    # Medium
            value = 90.0
        elif index == 3:    # Heavy
            value = 120.0
        else:
            return

        self.rebar_intensity_spin.blockSignals(True)
        self.rebar_intensity_spin.setValue(value)
        self.rebar_intensity_spin.blockSignals(False)




    def _calculate_and_update(self, show_dialogs: bool = True) -> None:
        """
        Core calculation path.

        If show_dialogs=False, we do NOT pop QMessageBoxes (used for auto-recalc after load).
        We simply bail out quietly on invalid inputs.
        """
        element_index = self.element_type_combo.currentIndex()

        try:
            vol_m3, form_area_m2 = self._calculate_geometry(element_index)
        except ValueError as exc:
            if show_dialogs:
                QtWidgets.QMessageBox.warning(self, "Invalid Input", str(exc))
            return

        # Materials & cost
        conc_density = float(self.conc_density_spin.value())      # kg/m³
        conc_cost = float(self.conc_cost_spin.value())            # USD/m³
        rebar_intensity = float(self.rebar_intensity_spin.value())  # kg/m³
        rebar_cost = float(self.rebar_cost_spin.value())          # USD/kg
        formwork_rate = float(self.formwork_rate_spin.value())    # USD/m²

        conc_weight_kg = vol_m3 * conc_density
        rebar_kg = vol_m3 * rebar_intensity
        rebar_tons = rebar_kg / 1000.0

        cost_conc = vol_m3 * conc_cost
        cost_rebar = rebar_kg * rebar_cost
        cost_form = form_area_m2 * formwork_rate
        total = cost_conc + cost_rebar + cost_form

        # Update UI
        self.lbl_volume.setText(f"{vol_m3:.3f} m³")
        self.lbl_form_area.setText(f"{form_area_m2:.2f} m²")
        self.lbl_rebar_kg.setText(f"{rebar_kg:,.0f} kg")
        self.lbl_rebar_tons.setText(f"{rebar_tons:.3f} t")
        self.lbl_conc_cost.setText(f"${cost_conc:,.2f}")
        self.lbl_rebar_cost.setText(f"${cost_rebar:,.2f}")
        self.lbl_total_cost.setText(f"${total:,.2f}")


    def _on_calculate_clicked(self) -> None:
        """Perform calculations for the selected element type (interactive, with dialogs)."""
        self._calculate_and_update(show_dialogs=True)


    def recalculate(self, show_dialogs: bool = False) -> None:
        """
        Public recalculation hook used by MainWindow after loading a project.
        Defaults to silent mode (no popups).
        """
        self._calculate_and_update(show_dialogs=show_dialogs)



    def _calculate_geometry(self, element_index: int) -> tuple[float, float]:
        """
        Calculate volume (m³) and approximate formwork area (m²)
        for the selected element type.

        Raises ValueError if any geometric input is non-positive
        where it must be.
        """
        if element_index == 0:
            # Slab / Base
            L = float(self.slab_length_spin.value())
            W = float(self.slab_width_spin.value())
            T_cm = float(self.slab_thickness_spin.value())
            N = int(self.slab_count_spin.value())

            T = T_cm / 100.0  # cm → m

            if L <= 0 or W <= 0 or T <= 0 or N <= 0:
                raise ValueError("For slabs, length, width, thickness and count must all be > 0.")

            vol_m3 = L * W * T * N
            form_area = 2.0 * (L + W) * T * N  # vertical sides

        elif element_index == 1:
            # Strip footing
            L = float(self.strip_length_spin.value())
            W = float(self.strip_width_spin.value())
            T_cm = float(self.strip_thickness_spin.value())

            T = T_cm / 100.0

            if L <= 0 or W <= 0 or T <= 0:
                raise ValueError("For strip footings, length, width and thickness must all be > 0.")

            vol_m3 = L * W * T
            # Approx: two long sides formed, ends ignored
            form_area = 2.0 * L * T

        elif element_index == 2:
            # Wall
            L = float(self.wall_length_spin.value())
            H = float(self.wall_height_spin.value())
            T_cm = float(self.wall_thickness_spin.value())
            N = int(self.wall_count_spin.value())

            T = T_cm / 100.0

            if L <= 0 or H <= 0 or T <= 0 or N <= 0:
                raise ValueError("For walls, length, height, thickness and count must all be > 0.")

            vol_m3 = L * H * T * N
            # Two faces formed, end faces ignored
            form_area = 2.0 * L * H * N

        elif element_index == 3:
            # Isolated footing
            L = float(self.iso_length_spin.value())
            W = float(self.iso_width_spin.value())
            T_cm = float(self.iso_thickness_spin.value())
            N = int(self.iso_count_spin.value())

            T = T_cm / 100.0

            if L <= 0 or W <= 0 or T <= 0 or N <= 0:
                raise ValueError(
                    "For isolated footings, length, width, thickness and count must all be > 0."
                )

            vol_m3 = L * W * T * N
            form_area = 2.0 * (L + W) * T * N  # four vertical sides

        else:
            raise ValueError("Unknown element type index.")

        return vol_m3, form_area

    def _on_reset_clicked(self) -> None:
        """Reset all inputs and results to default values."""

        # Reset geometry for each element
        self.slab_length_spin.setValue(0.0)
        self.slab_width_spin.setValue(0.0)
        self.slab_thickness_spin.setValue(0.0)
        self.slab_count_spin.setValue(1)

        self.strip_length_spin.setValue(0.0)
        self.strip_width_spin.setValue(0.0)
        self.strip_thickness_spin.setValue(0.0)

        self.wall_length_spin.setValue(0.0)
        self.wall_height_spin.setValue(0.0)
        self.wall_thickness_spin.setValue(0.0)
        self.wall_count_spin.setValue(1)

        self.iso_length_spin.setValue(0.0)
        self.iso_width_spin.setValue(0.0)
        self.iso_thickness_spin.setValue(0.0)
        self.iso_count_spin.setValue(1)

        # Reset materials
        self.conc_density_spin.setValue(2400.0)
        self.conc_cost_spin.setValue(60.0)
        self.rebar_intensity_spin.setValue(100.0)
        self.rebar_level_combo.setCurrentIndex(0)  # Custom
        self.rebar_cost_spin.setValue(640.0)

        # Clear results
        self.lbl_volume.setText("0.000 m³")
        self.lbl_conc_weight.setText("0 kg")
        self.lbl_form_area.setText("0.00 m²")
        self.lbl_rebar_kg.setText("0 kg")
        self.lbl_rebar_tons.setText("0.000 t")
        self.lbl_conc_cost.setText("$0.00")
        self.lbl_rebar_cost.setText("$0.00")
        self.lbl_total_cost.setText("$0.00")

        # Reset element description to current selection
        self._update_element_description(self.element_type_combo.currentIndex())
