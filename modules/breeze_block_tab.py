




"""
breeze_block_tab.py

PyQt5 widget implementing a breeze block / hollow concrete block
calculator for walls, half-circle arcs, and raceway reactors.

Features
--------
- Drop-down for block sizes (from block_data.py).
- Inputs for straight wall length, height and count.
- Inputs for half-circle arc radius, height and count.
- Inputs for reactors (raceways) with length, width, height and count.

  Reactor model:
    Each reactor is assumed to have:
      * two long outer side walls of length L
      * one central wall of length L (only along the straight section)
      * two end arches, each a half-circle with radius = W/2
        (diameter equal to reactor width).

    So the total wall area per reactor is:
        A_reactor = H * (3*L + 2*π*R)
    where L is reactor length, W is reactor width, R = W/2, H is wall height.

- Cost per block in USD with a reasonable default based on selected size.
- Computes:
    * straight wall area
    * arc wall area (generic half-circle arcs)
    * reactor wall area (per geometry above)
    * total area (all of the above)
    * number of blocks (rounded up)
    * pallets required (rounded up)
    * leftover blocks on last pallet
    * total cost (USD)
"""

import math
from typing import Optional

from PyQt5 import QtCore, QtWidgets

# from block_data import get_block_names, get_block_type, BlockType
from .block_data import get_block_names, get_block_type, BlockType



class BreezeBlockTab(QtWidgets.QWidget):
    """
    Main widget for the breeze block calculator tab.
    Designed to be dropped into a QTabWidget.
    """


    # ------------------------------------------------------------------
    # Project Save/Load
    # ------------------------------------------------------------------

    def export_state(self) -> dict:
        return {
            "block_name": self.block_combo.currentText(),
            "cost_per_block": float(self.cost_per_block_spin.value()),
            "wall_length": float(self.wall_length_spin.value()),
            "wall_height": float(self.wall_height_spin.value()),
            "wall_count": int(self.wall_count_spin.value()),
            "arc_radius": float(self.arc_radius_spin.value()),
            "arc_height": float(self.arc_height_spin.value()),
            "arc_count": int(self.arc_count_spin.value()),
            "reactor_length": float(self.reactor_length_spin.value()),
            "reactor_width": float(self.reactor_width_spin.value()),
            "reactor_height": float(self.reactor_height_spin.value()),
            "reactor_count": int(self.reactor_count_spin.value()),
        }

    def import_state(self, state: dict) -> None:
        if not isinstance(state, dict):
            return

        # Block selection first (because it can auto-update cost defaults)
        block_name = state.get("block_name", None)
        if isinstance(block_name, str) and block_name:
            idx = self.block_combo.findText(block_name)
            if idx >= 0:
                self.block_combo.setCurrentIndex(idx)

        # Now apply values
        self.cost_per_block_spin.setValue(float(state.get("cost_per_block", self.cost_per_block_spin.value())))

        self.wall_length_spin.setValue(float(state.get("wall_length", 0.0)))
        self.wall_height_spin.setValue(float(state.get("wall_height", 0.0)))
        self.wall_count_spin.setValue(int(state.get("wall_count", 1)))

        self.arc_radius_spin.setValue(float(state.get("arc_radius", 0.0)))
        self.arc_height_spin.setValue(float(state.get("arc_height", 0.0)))
        self.arc_count_spin.setValue(int(state.get("arc_count", 0)))

        self.reactor_length_spin.setValue(float(state.get("reactor_length", 0.0)))
        self.reactor_width_spin.setValue(float(state.get("reactor_width", 0.0)))
        self.reactor_height_spin.setValue(float(state.get("reactor_height", 0.0)))
        self.reactor_count_spin.setValue(int(state.get("reactor_count", 0)))





    def __init__(self, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        self._current_block: Optional[BlockType] = None
        self._build_ui()
        self._connect_signals()
        self._load_initial_block_type()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------



    def _build_ui(self) -> None:
        """Create all widgets and layouts, wrapped in a scroll area."""

        # ------ OUTER LAYOUT ------
        outer_layout = QtWidgets.QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)

        # Scroll Area
        scroll_area = QtWidgets.QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QtWidgets.QFrame.NoFrame)

        # Inner content widget
        content_widget = QtWidgets.QWidget(scroll_area)
        content_layout = QtWidgets.QVBoxLayout(content_widget)
        content_layout.setContentsMargins(12, 12, 12, 12)
        content_layout.setSpacing(10)


        # -------- Block selection + cost --------
        block_group = QtWidgets.QGroupBox("Block Selection", content_widget)
        block_group_layout = QtWidgets.QGridLayout(block_group)
        block_group_layout.setColumnStretch(1, 1)

        self.block_combo = QtWidgets.QComboBox(block_group)
        self.block_combo.addItems(get_block_names())
        self.block_combo.setMinimumWidth(220)

        self.cost_per_block_spin = QtWidgets.QDoubleSpinBox(block_group)
        self.cost_per_block_spin.setSuffix(" USD")
        self.cost_per_block_spin.setDecimals(4)
        self.cost_per_block_spin.setRange(0.0, 100.0)
        self.cost_per_block_spin.setSingleStep(0.05)

        block_group_layout.addWidget(QtWidgets.QLabel("Block size:"), 0, 0)
        block_group_layout.addWidget(self.block_combo, 0, 1)
        block_group_layout.addWidget(QtWidgets.QLabel("Cost per block:"), 1, 0)
        block_group_layout.addWidget(self.cost_per_block_spin, 1, 1)

        # -------- Straight wall inputs --------
        wall_group = QtWidgets.QGroupBox("Straight Walls", content_widget)
        wall_form = QtWidgets.QFormLayout(wall_group)
        wall_form.setLabelAlignment(QtCore.Qt.AlignRight)

        self.wall_length_spin = QtWidgets.QDoubleSpinBox(wall_group)
        self.wall_length_spin.setSuffix(" m")
        self.wall_length_spin.setDecimals(3)
        self.wall_length_spin.setRange(0.0, 1000.0)

        self.wall_height_spin = QtWidgets.QDoubleSpinBox(wall_group)
        self.wall_height_spin.setSuffix(" m")
        self.wall_height_spin.setDecimals(3)
        self.wall_height_spin.setRange(0.0, 100.0)

        self.wall_count_spin = QtWidgets.QSpinBox(wall_group)
        self.wall_count_spin.setRange(0, 9999)
        self.wall_count_spin.setValue(1)

        wall_form.addRow("Wall length:", self.wall_length_spin)
        wall_form.addRow("Wall height:", self.wall_height_spin)
        wall_form.addRow("Number of walls:", self.wall_count_spin)

        # -------- Arc inputs --------
        arc_group = QtWidgets.QGroupBox("Half-circle Arcs (General)", content_widget)
        arc_form = QtWidgets.QFormLayout(arc_group)
        arc_form.setLabelAlignment(QtCore.Qt.AlignRight)

        self.arc_radius_spin = QtWidgets.QDoubleSpinBox(arc_group)
        self.arc_radius_spin.setSuffix(" m")
        self.arc_radius_spin.setDecimals(3)
        self.arc_radius_spin.setRange(0.0, 1000.0)

        self.arc_height_spin = QtWidgets.QDoubleSpinBox(arc_group)
        self.arc_height_spin.setSuffix(" m")
        self.arc_height_spin.setDecimals(3)
        self.arc_height_spin.setRange(0.0, 100.0)

        self.arc_count_spin = QtWidgets.QSpinBox(arc_group)
        self.arc_count_spin.setRange(0, 9999)
        self.arc_count_spin.setValue(0)

        arc_form.addRow("Arc radius:", self.arc_radius_spin)
        arc_form.addRow("Arc height:", self.arc_height_spin)
        arc_form.addRow("Number of arcs:", self.arc_count_spin)

        # -------- Reactor inputs --------
        reactor_group = QtWidgets.QGroupBox("Reactors (Raceway Walls)", content_widget)
        reactor_form = QtWidgets.QFormLayout(reactor_group)
        reactor_form.setLabelAlignment(QtCore.Qt.AlignRight)

        self.reactor_length_spin = QtWidgets.QDoubleSpinBox(reactor_group)
        self.reactor_length_spin.setSuffix(" m")
        self.reactor_length_spin.setDecimals(3)
        self.reactor_length_spin.setRange(0.0, 10000.0)

        self.reactor_width_spin = QtWidgets.QDoubleSpinBox(reactor_group)
        self.reactor_width_spin.setSuffix(" m")
        self.reactor_width_spin.setDecimals(3)
        self.reactor_width_spin.setRange(0.0, 10000.0)

        self.reactor_height_spin = QtWidgets.QDoubleSpinBox(reactor_group)
        self.reactor_height_spin.setSuffix(" m")
        self.reactor_height_spin.setDecimals(3)
        self.reactor_height_spin.setRange(0.0, 100.0)

        self.reactor_count_spin = QtWidgets.QSpinBox(reactor_group)
        self.reactor_count_spin.setRange(0, 9999)
        self.reactor_count_spin.setValue(0)

        reactor_form.addRow("Reactor length L:", self.reactor_length_spin)
        reactor_form.addRow("Reactor width W:", self.reactor_width_spin)
        reactor_form.addRow("Reactor wall height H:", self.reactor_height_spin)
        reactor_form.addRow("Number of reactors:", self.reactor_count_spin)

        reactor_note = QtWidgets.QLabel(
            "Reactor geometry:\n"
            "• 2 long side walls (L)\n"
            "• 1 central straight wall (L)\n"
            "• 2 end arches (half-circles, radius = W/2)\n"
            "Total wall area per reactor: A = H * (3·L + 2·π·(W/2))"
        )
        reactor_note.setWordWrap(True)

        # -------- Buttons --------
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addStretch(1)

        self.reset_button = QtWidgets.QPushButton("Reset", content_widget)
        self.reset_button.setObjectName("secondaryButton")

        self.calculate_button = QtWidgets.QPushButton("Calculate", content_widget)
        self.calculate_button.setObjectName("primaryButton")

        button_layout.addWidget(self.reset_button)
        button_layout.addWidget(self.calculate_button)

        # -------- Results --------
        result_group = QtWidgets.QGroupBox("Results", content_widget)
        result_layout = QtWidgets.QFormLayout(result_group)
        result_layout.setLabelAlignment(QtCore.Qt.AlignRight)

        self.lbl_wall_area = QtWidgets.QLabel("0.00 m²", content_widget)
        self.lbl_arc_area = QtWidgets.QLabel("0.00 m²", content_widget)
        self.lbl_reactor_area = QtWidgets.QLabel("0.00 m²", content_widget)
        self.lbl_total_area = QtWidgets.QLabel("0.00 m²", content_widget)
        self.lbl_blocks = QtWidgets.QLabel("0 blocks", content_widget)
        self.lbl_pallets = QtWidgets.QLabel("0 pallets", content_widget)
        self.lbl_leftover = QtWidgets.QLabel("0 blocks", content_widget)
        self.lbl_total_cost = QtWidgets.QLabel("$0.00", content_widget)

        result_layout.addRow("Straight wall area:", self.lbl_wall_area)
        result_layout.addRow("Arc wall area:", self.lbl_arc_area)
        result_layout.addRow("Reactor wall area:", self.lbl_reactor_area)
        result_layout.addRow("Total area:", self.lbl_total_area)
        result_layout.addRow("Blocks required:", self.lbl_blocks)
        result_layout.addRow("Pallets required:", self.lbl_pallets)
        result_layout.addRow("Leftover blocks:", self.lbl_leftover)
        result_layout.addRow("Total cost:", self.lbl_total_cost)

        # -------- Add groups to scrollable layout --------
        content_layout.addWidget(block_group)
        content_layout.addWidget(wall_group)
        content_layout.addWidget(arc_group)
        content_layout.addWidget(reactor_group)
        content_layout.addWidget(reactor_note)
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
        self.block_combo.currentTextChanged.connect(self._on_block_changed)
        self.calculate_button.clicked.connect(self._on_calculate_clicked)
        self.reset_button.clicked.connect(self._on_reset_clicked)

    # ------------------------------------------------------------------
    # Initial state / helpers
    # ------------------------------------------------------------------

    def _load_initial_block_type(self) -> None:
        """Load the first block type as the default selection."""
        if self.block_combo.count() > 0:
            name = self.block_combo.currentText()
            self._apply_block_type(name)

    def _on_block_changed(self, name: str) -> None:
        """Handle change of selected block type."""
        self._apply_block_type(name)

    def _apply_block_type(self, name: str) -> None:
        """
        Update internal BlockType and reset cost spinner
        to default for that block.
        """
        try:
            block = get_block_type(name)
        except KeyError:
            self._current_block = None
            return

        self._current_block = block
        # Set default cost but don't block user edits later.
        self.cost_per_block_spin.blockSignals(True)
        self.cost_per_block_spin.setValue(block.default_cost_usd)
        self.cost_per_block_spin.blockSignals(False)

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    def _on_calculate_clicked(self) -> None:
        """Perform the block, pallet and cost calculations."""

        if self._current_block is None:
            QtWidgets.QMessageBox.warning(
                self,
                "No Block Type",
                "Please select a block size before calculating.",
            )
            return

        block = self._current_block

        # -------- Gather input values --------
        # Straight walls
        wall_length = float(self.wall_length_spin.value())
        wall_height = float(self.wall_height_spin.value())
        wall_count = int(self.wall_count_spin.value())

        # Generic arcs
        arc_radius = float(self.arc_radius_spin.value())
        arc_height = float(self.arc_height_spin.value())
        arc_count = int(self.arc_count_spin.value())

        # Reactors
        reactor_length = float(self.reactor_length_spin.value())
        reactor_width = float(self.reactor_width_spin.value())
        reactor_height = float(self.reactor_height_spin.value())
        reactor_count = int(self.reactor_count_spin.value())

        cost_per_block = float(self.cost_per_block_spin.value())

        # -------- Compute wall areas --------
        # Straight walls
        if wall_length > 0 and wall_height > 0 and wall_count > 0:
            wall_area = wall_length * wall_height * wall_count
        else:
            wall_area = 0.0

        # Generic half-circle arcs: arc length = π * radius, area = length * height
        if arc_radius > 0 and arc_height > 0 and arc_count > 0:
            arc_area_per = math.pi * arc_radius * arc_height
            arc_area_total = arc_area_per * arc_count
        else:
            arc_area_total = 0.0

        # Reactors: two long walls + central wall (all length L) + two end arches (radius W/2)
        if (
            reactor_length > 0
            and reactor_width > 0
            and reactor_height > 0
            and reactor_count > 0
        ):
            R = reactor_width / 2.0  # radius of each end arch
            # Total straight length per reactor: 3 * L
            straight_length = 3.0 * reactor_length
            # Total arch length per reactor: 2 * (π * R)
            arch_length = 2.0 * math.pi * R
            wall_length_per_reactor = straight_length + arch_length
            reactor_area_total = wall_length_per_reactor * reactor_height * reactor_count
        else:
            reactor_area_total = 0.0

        total_area = wall_area + arc_area_total + reactor_area_total

        # -------- Compute blocks and pallets --------
        block_face_area = block.length_m * block.height_m
        if block_face_area > 0 and total_area > 0:
            blocks_required = math.ceil(total_area / block_face_area)
        else:
            blocks_required = 0

        blocks_per_pallet = max(1, block.blocks_per_pallet)
        if blocks_required > 0:
            pallets_required = math.ceil(blocks_required / blocks_per_pallet)
            leftover_blocks = pallets_required * blocks_per_pallet - blocks_required
        else:
            pallets_required = 0
            leftover_blocks = 0

        total_cost = blocks_required * cost_per_block

        # -------- Update labels --------
        self.lbl_wall_area.setText(f"{wall_area:,.2f} m²")
        self.lbl_arc_area.setText(f"{arc_area_total:,.2f} m²")
        self.lbl_reactor_area.setText(f"{reactor_area_total:,.2f} m²")
        self.lbl_total_area.setText(f"{total_area:,.2f} m²")
        self.lbl_blocks.setText(f"{blocks_required:,d} blocks")
        self.lbl_pallets.setText(f"{pallets_required:,d} pallets")
        self.lbl_leftover.setText(f"{leftover_blocks:,d} blocks")
        self.lbl_total_cost.setText(f"${total_cost:,.2f}")

    def _on_reset_clicked(self) -> None:
        """
        Reset all inputs to sensible defaults and clear results.
        """
        # Straight walls
        self.wall_length_spin.setValue(0.0)
        self.wall_height_spin.setValue(0.0)
        self.wall_count_spin.setValue(1)

        # Generic arcs
        self.arc_radius_spin.setValue(0.0)
        self.arc_height_spin.setValue(0.0)
        self.arc_count_spin.setValue(0)

        # Reactors
        self.reactor_length_spin.setValue(0.0)
        self.reactor_width_spin.setValue(0.0)
        self.reactor_height_spin.setValue(0.0)
        self.reactor_count_spin.setValue(0)

        # Reset cost to default for selected block
        if self._current_block is not None:
            self.cost_per_block_spin.setValue(self._current_block.default_cost_usd)

        # Clear results
        self.lbl_wall_area.setText("0.00 m²")
        self.lbl_arc_area.setText("0.00 m²")
        self.lbl_reactor_area.setText("0.00 m²")
        self.lbl_total_area.setText("0.00 m²")
        self.lbl_blocks.setText("0 blocks")
        self.lbl_pallets.setText("0 pallets")
        self.lbl_leftover.setText("0 blocks")
        self.lbl_total_cost.setText("$0.00")















