
"""
land_prep_tab.py

PyQt5 widget implementing a land preparation calculator for:
- Preparing and compacting a surface platform area.
- Excavating reactor trench areas to a given depth.
- Re-compacting the trench base and sides.

The goal is to get:
- Earthworks volumes (cut and compacted fill).
- Approximate compaction effort (m² and passes).
- Cost estimates for excavation and compaction.

High-level model
----------------
1) Platform preparation
   - A rectangular (or equivalent) area A_site [m²] is prepared.
   - Preparation depth H_site_cm [cm] is applied as an "improvement" depth
     (e.g. scarify, re-level and re-compact).
   - We estimate a "disturbed" volume:
         V_site = A_site * H_site
     where H_site = H_site_cm / 100 [m].

2) Reactor trenches
   - Trenches are approximated as rectangular strips:
       * total trench length L_trench [m]
       * trench width W_trench [m]
       * trench depth H_trench_cm [cm], H_trench = H_trench_cm / 100 [m]
       * number of identical trenches N_trench
   - Excavation (cut) volume:
         V_trench = L_trench * W_trench * H_trench * N_trench

3) Combined volumes
   - Total cut volume:
         V_cut_total = V_site + V_trench
     (You may choose to treat V_site as "reworked" rather than new cut; this
      tool simply reports the combined disturbed soil volume.)

4) Compaction modelling
   - Target compaction is expressed as a percentage factor, e.g. 95% of the
     design dry density (Proctor). This does not directly affect volume but
     is included so the user can record / specify the compaction level.
   - Compaction is typically done in "lifts" of thickness H_lift [m]
     (user specified in cm). For each lift, the roller makes a number of
     passes P_per_lift over the area.

   - Platform area compaction:
       * compacted area A_comp_platform = A_site

   - Trench compaction:
       * base area (bottom): A_trench_base = L_trench * W_trench * N_trench
       * side walls: 2 sides along length:
             A_trench_sides ≈ 2 * L_trench * H_trench * N_trench
         (ignoring the end faces for simplicity).

       * Total trench compaction area:
             A_comp_trench = A_trench_base + A_trench_sides

   - Total compaction area:
         A_comp_total = A_comp_platform + A_comp_trench

   - Number of lifts for the platform:
         n_lifts_platform = ceil(H_site / H_lift)
     (if H_site and H_lift > 0)

   - Number of lifts for trenches:
         n_lifts_trench = ceil(H_trench / H_lift)

   - Total "area * passes" for compaction:
         A_pass_platform = A_comp_platform * n_lifts_platform * P_per_lift
         A_pass_trench   = A_comp_trench   * n_lifts_trench   * P_per_lift
         A_pass_total    = A_pass_platform + A_pass_trench

5) Costs
   - Excavation (cut) cost:
         cost_cut = V_cut_total * cost_per_m3_cut

   - Compaction cost (if charged per m² per pass):
         cost_compaction = A_pass_total * cost_per_m2_pass

   - Total:
         cost_total = cost_cut + cost_compaction
"""

import math
from typing import Optional

from PyQt5 import QtCore, QtWidgets


class LandPrepTab(QtWidgets.QWidget):
    """
    Main widget for the land preparation calculator tab.
    Designed to be dropped into a QTabWidget.
    Now wrapped in a QScrollArea so the content can scroll
    on smaller screens.
    """


# ------------------------------------------------------------------
# Project Save/Load
# ------------------------------------------------------------------

    def export_state(self) -> dict:
        """
        Return a JSON-serializable snapshot of LandPrepTab inputs.

        IMPORTANT:
        Keep these keys stable (for project file compatibility),
        but always reference the REAL widget attribute names defined in _build_ui().
        """
        return {
            # Platform
            "site_area": float(self.site_area_spin.value()),
            "site_depth_cm": float(self.site_depth_spin.value()),

            # Trenches
            "trench_length": float(self.trench_length_spin.value()),
            "trench_width": float(self.trench_width_spin.value()),
            "trench_depth_cm": float(self.trench_depth_spin.value()),
            "trench_count": int(self.trench_count_spin.value()),

            # Compaction settings
            "compaction_target_pct": float(self.compaction_target_spin.value()),
            "lift_thickness_cm": float(self.lift_thickness_spin.value()),
            "passes_per_lift": int(self.passes_per_lift_spin.value()),

            # Costs
            "cost_per_m3_cut": float(self.cost_per_m3_cut_spin.value()),
            "cost_per_m2_pass": float(self.cost_per_m2_pass_spin.value()),
        }

    def import_state(self, state: dict) -> None:
        """
        Restore LandPrepTab inputs from a saved project snapshot.
        """
        if not isinstance(state, dict):
            return

        # Platform
        self.site_area_spin.setValue(float(state.get("site_area", 0.0)))
        self.site_depth_spin.setValue(float(state.get("site_depth_cm", 0.0)))

        # Trenches
        self.trench_length_spin.setValue(float(state.get("trench_length", 0.0)))
        self.trench_width_spin.setValue(float(state.get("trench_width", 0.0)))
        self.trench_depth_spin.setValue(float(state.get("trench_depth_cm", 0.0)))

        # trench_count_spin has a minimum of 1 in the UI, so don't import 0 accidentally
        trench_count = int(state.get("trench_count", 1))
        self.trench_count_spin.setValue(max(1, trench_count))

        # Compaction settings
        self.compaction_target_spin.setValue(
            float(state.get("compaction_target_pct", self.compaction_target_spin.value()))
        )
        self.lift_thickness_spin.setValue(
            float(state.get("lift_thickness_cm", self.lift_thickness_spin.value()))
        )
        self.passes_per_lift_spin.setValue(
            max(1, int(state.get("passes_per_lift", self.passes_per_lift_spin.value())))
        )

        # Costs
        self.cost_per_m3_cut_spin.setValue(
            float(state.get("cost_per_m3_cut", self.cost_per_m3_cut_spin.value()))
        )
        self.cost_per_m2_pass_spin.setValue(
            float(state.get("cost_per_m2_pass", self.cost_per_m2_pass_spin.value()))
        )



    def __init__(self, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        self._build_ui()
        self._connect_signals()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        """
        Build the UI with a scrollable content area.

        Outer layout: a single QScrollArea filling this tab.
        Inner widget: holds all groups (platform, trench, compaction, cost, results)
        in a vertical layout.
        """
        # Outer layout for the tab itself
        outer_layout = QtWidgets.QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)

        # Scroll area
        scroll_area = QtWidgets.QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QtWidgets.QFrame.NoFrame)

        # Inner content widget inside the scroll area
        content_widget = QtWidgets.QWidget(scroll_area)
        content_layout = QtWidgets.QVBoxLayout(content_widget)
        content_layout.setContentsMargins(12, 12, 12, 12)
        content_layout.setSpacing(10)

        # ---------------- Land preparation geometry ----------------
        prep_group = QtWidgets.QGroupBox("Platform Preparation (General Area)", content_widget)
        prep_form = QtWidgets.QFormLayout(prep_group)
        prep_form.setLabelAlignment(QtCore.Qt.AlignRight)

        # Site plan area in m²
        self.site_area_spin = QtWidgets.QDoubleSpinBox(prep_group)
        self.site_area_spin.setSuffix(" m²")
        self.site_area_spin.setDecimals(1)
        self.site_area_spin.setRange(0.0, 1_000_000.0)
        self.site_area_spin.setSingleStep(10.0)

        # Preparation depth in cm
        self.site_depth_spin = QtWidgets.QDoubleSpinBox(prep_group)
        self.site_depth_spin.setSuffix(" cm")
        self.site_depth_spin.setDecimals(1)
        self.site_depth_spin.setRange(0.0, 500.0)
        self.site_depth_spin.setSingleStep(1.0)

        prep_form.addRow("Platform plan area:", self.site_area_spin)
        prep_form.addRow("Preparation depth:", self.site_depth_spin)

        # Explanatory label
        prep_note = QtWidgets.QLabel(
            "Platform preparation: area to be levelled, trimmed and compacted "
            "before installing reactors or foundations. Depth is the thickness "
            "of soil that is reworked (e.g. scarified and re-compacted).",
            content_widget,
        )
        prep_note.setWordWrap(True)

        # ---------------- Reactor trench geometry ----------------
        trench_group = QtWidgets.QGroupBox("Reactor Trenches (Excavation and Re-compaction)", content_widget)
        trench_form = QtWidgets.QFormLayout(trench_group)
        trench_form.setLabelAlignment(QtCore.Qt.AlignRight)

        # Total trench length across all reactors (m)
        self.trench_length_spin = QtWidgets.QDoubleSpinBox(trench_group)
        self.trench_length_spin.setSuffix(" m")
        self.trench_length_spin.setDecimals(2)
        self.trench_length_spin.setRange(0.0, 100_000.0)
        self.trench_length_spin.setSingleStep(1.0)

        # Trench width (m)
        self.trench_width_spin = QtWidgets.QDoubleSpinBox(trench_group)
        self.trench_width_spin.setSuffix(" m")
        self.trench_width_spin.setDecimals(3)
        self.trench_width_spin.setRange(0.0, 1000.0)
        self.trench_width_spin.setSingleStep(0.1)

        # Trench depth (cm)
        self.trench_depth_spin = QtWidgets.QDoubleSpinBox(trench_group)
        self.trench_depth_spin.setSuffix(" cm")
        self.trench_depth_spin.setDecimals(1)
        self.trench_depth_spin.setRange(0.0, 1000.0)
        self.trench_depth_spin.setSingleStep(1.0)

        # Number of identical trenches (reactor lanes)
        self.trench_count_spin = QtWidgets.QSpinBox(trench_group)
        self.trench_count_spin.setRange(1, 10_000)
        self.trench_count_spin.setValue(1)

        trench_form.addRow("Total trench length L (all reactors):", self.trench_length_spin)
        trench_form.addRow("Trench width W:", self.trench_width_spin)
        trench_form.addRow("Trench depth H:", self.trench_depth_spin)
        trench_form.addRow("Number of trenches:", self.trench_count_spin)

        trench_note = QtWidgets.QLabel(
            "Trenches are approximated as long rectangular cuts for services or "
            "reactor base zones. Depth is measured from the compacted platform level. "
            "Total length can be the sum of all reactor lanes.",
            content_widget,
        )
        trench_note.setWordWrap(True)

        # ---------------- Compaction parameters ----------------
        comp_group = QtWidgets.QGroupBox("Compaction Parameters", content_widget)
        comp_form = QtWidgets.QFormLayout(comp_group)
        comp_form.setLabelAlignment(QtCore.Qt.AlignRight)

        # Target compaction (e.g. 95% Proctor)
        self.compaction_target_spin = QtWidgets.QDoubleSpinBox(comp_group)
        self.compaction_target_spin.setSuffix(" %")
        self.compaction_target_spin.setDecimals(1)
        self.compaction_target_spin.setRange(80.0, 110.0)
        self.compaction_target_spin.setSingleStep(0.5)
        self.compaction_target_spin.setValue(95.0)

        # Compaction lift thickness (cm)
        self.lift_thickness_spin = QtWidgets.QDoubleSpinBox(comp_group)
        self.lift_thickness_spin.setSuffix(" cm")
        self.lift_thickness_spin.setDecimals(1)
        self.lift_thickness_spin.setRange(1.0, 100.0)
        self.lift_thickness_spin.setSingleStep(1.0)
        self.lift_thickness_spin.setValue(20.0)

        # Roller / compactor effective width (m)
        self.roller_width_spin = QtWidgets.QDoubleSpinBox(comp_group)
        self.roller_width_spin.setSuffix(" m")
        self.roller_width_spin.setDecimals(2)
        self.roller_width_spin.setRange(0.1, 10.0)
        self.roller_width_spin.setSingleStep(0.1)
        self.roller_width_spin.setValue(2.0)

        # Passes per lift
        self.passes_per_lift_spin = QtWidgets.QSpinBox(comp_group)
        self.passes_per_lift_spin.setRange(1, 50)
        self.passes_per_lift_spin.setValue(4)

        comp_form.addRow("Target compaction (ref. Proctor):", self.compaction_target_spin)
        comp_form.addRow("Compaction lift thickness:", self.lift_thickness_spin)
        comp_form.addRow("Roller effective width:", self.roller_width_spin)
        comp_form.addRow("Passes per lift:", self.passes_per_lift_spin)

        comp_note = QtWidgets.QLabel(
            "Compaction is modelled in lifts: each lift of soil is compacted with a "
            "certain number of passes. This is a planning/estimation tool; always "
            "verify with on-site testing (e.g. field density tests).",
            content_widget,
        )
        comp_note.setWordWrap(True)

        # ---------------- Cost inputs ----------------
        cost_group = QtWidgets.QGroupBox("Cost Inputs", content_widget)
        cost_form = QtWidgets.QFormLayout(cost_group)
        cost_form.setLabelAlignment(QtCore.Qt.AlignRight)

        # Excavation cost per m³ (USD)
        self.cost_per_m3_cut_spin = QtWidgets.QDoubleSpinBox(cost_group)
        self.cost_per_m3_cut_spin.setSuffix(" USD/m³")
        self.cost_per_m3_cut_spin.setDecimals(2)
        self.cost_per_m3_cut_spin.setRange(0.0, 1000.0)
        self.cost_per_m3_cut_spin.setSingleStep(1.0)
        # Example default: around 2 – 4 USD/m³ for bulk earthwork; override as needed.
        self.cost_per_m3_cut_spin.setValue(3.0)

        # Compaction cost per m² per pass (USD)
        self.cost_per_m2_pass_spin = QtWidgets.QDoubleSpinBox(cost_group)
        self.cost_per_m2_pass_spin.setSuffix(" USD/(m²·pass)")
        self.cost_per_m2_pass_spin.setDecimals(4)
        self.cost_per_m2_pass_spin.setRange(0.0, 10.0)
        self.cost_per_m2_pass_spin.setSingleStep(0.01)
        # Example default: 0.01 USD per m² per pass (i.e. 0.04 USD/m² for 4 passes).
        self.cost_per_m2_pass_spin.setValue(0.01)

        cost_form.addRow("Excavation cost:", self.cost_per_m3_cut_spin)
        cost_form.addRow("Compaction cost:", self.cost_per_m2_pass_spin)

        cost_note = QtWidgets.QLabel(
            "Use your own project unit rates if available (e.g. from contractor "
            "quotations or historical data). This tool just multiplies volumes and "
            "areas by the rates you provide.",
            content_widget,
        )
        cost_note.setWordWrap(True)

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

        self.lbl_site_volume = QtWidgets.QLabel("0.000 m³", result_group)
        self.lbl_trench_volume = QtWidgets.QLabel("0.000 m³", result_group)
        self.lbl_total_cut_volume = QtWidgets.QLabel("0.000 m³", result_group)

        self.lbl_platform_comp_area = QtWidgets.QLabel("0.00 m²", result_group)
        self.lbl_trench_comp_area = QtWidgets.QLabel("0.00 m²", result_group)
        self.lbl_total_comp_area = QtWidgets.QLabel("0.00 m²", result_group)

        self.lbl_lifts_platform = QtWidgets.QLabel("0", result_group)
        self.lbl_lifts_trench = QtWidgets.QLabel("0", result_group)
        self.lbl_total_area_passes = QtWidgets.QLabel("0.00 m²·passes", result_group)

        self.lbl_cut_cost = QtWidgets.QLabel("$0.00", result_group)
        self.lbl_compaction_cost = QtWidgets.QLabel("$0.00", result_group)
        self.lbl_total_cost = QtWidgets.QLabel("$0.00", result_group)

        result_form.addRow("Platform disturbed volume:", self.lbl_site_volume)
        result_form.addRow("Trench excavation volume:", self.lbl_trench_volume)
        result_form.addRow("Total cut volume:", self.lbl_total_cut_volume)

        result_form.addRow("Platform compaction area:", self.lbl_platform_comp_area)
        result_form.addRow("Trench compaction area:", self.lbl_trench_comp_area)
        result_form.addRow("Total compaction area:", self.lbl_total_comp_area)

        result_form.addRow("Platform lifts:", self.lbl_lifts_platform)
        result_form.addRow("Trench lifts:", self.lbl_lifts_trench)
        result_form.addRow("Total area × passes:", self.lbl_total_area_passes)

        result_form.addRow("Excavation cost:", self.lbl_cut_cost)
        result_form.addRow("Compaction cost:", self.lbl_compaction_cost)
        result_form.addRow("Total land prep cost:", self.lbl_total_cost)

        # ---------------- Add everything to the content layout ----------------
        content_layout.addWidget(prep_group)
        content_layout.addWidget(prep_note)
        content_layout.addWidget(trench_group)
        content_layout.addWidget(trench_note)
        content_layout.addWidget(comp_group)
        content_layout.addWidget(comp_note)
        content_layout.addWidget(cost_group)
        content_layout.addWidget(cost_note)
        content_layout.addLayout(button_layout)
        content_layout.addWidget(result_group)
        content_layout.addStretch(1)

        # Wire the content widget into the scroll area
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
        """Compute volumes, compaction effort and costs."""

        # --- Read platform inputs ---
        A_site = float(self.site_area_spin.value())          # m²
        H_site_cm = float(self.site_depth_spin.value())      # cm
        H_site = H_site_cm / 100.0                           # m

        # --- Read trench inputs ---
        L_trench = float(self.trench_length_spin.value())    # m
        W_trench = float(self.trench_width_spin.value())     # m
        H_trench_cm = float(self.trench_depth_spin.value())  # cm
        H_trench = H_trench_cm / 100.0                       # m
        N_trench = int(self.trench_count_spin.value())

        # --- Compaction inputs ---
        target_compaction = float(self.compaction_target_spin.value())  # %
        H_lift_cm = float(self.lift_thickness_spin.value())             # cm
        H_lift = H_lift_cm / 100.0                                      # m
        passes_per_lift = int(self.passes_per_lift_spin.value())

        # --- Cost inputs ---
        cost_per_m3_cut = float(self.cost_per_m3_cut_spin.value())
        cost_per_m2_pass = float(self.cost_per_m2_pass_spin.value())

        # Basic validation
        if A_site < 0 or H_site < 0 or L_trench < 0 or W_trench < 0 or H_trench < 0:
            QtWidgets.QMessageBox.warning(
                self,
                "Invalid Input",
                "Areas, lengths and depths cannot be negative.",
            )
            return

        if N_trench <= 0:
            QtWidgets.QMessageBox.warning(
                self,
                "Invalid Input",
                "Number of trenches must be at least 1.",
            )
            return

        if H_lift <= 0:
            QtWidgets.QMessageBox.warning(
                self,
                "Invalid Input",
                "Compaction lift thickness must be > 0.",
            )
            return

        if passes_per_lift <= 0:
            QtWidgets.QMessageBox.warning(
                self,
                "Invalid Input",
                "Passes per lift must be at least 1.",
            )
            return

        # --- Volumes ---
        # Platform disturbed volume
        V_site = A_site * H_site

        # Trench volume
        V_trench = L_trench * W_trench * H_trench * N_trench

        # Total cut volume
        V_cut_total = V_site + V_trench

        # --- Compaction areas ---
        # Platform compaction area is just the platform plan area
        A_comp_platform = A_site

        # Trench base area
        A_trench_base = L_trench * W_trench * N_trench

        # Trench side walls (2 long sides per trench, ignoring ends)
        A_trench_sides = 2.0 * L_trench * H_trench * N_trench

        A_comp_trench = A_trench_base + A_trench_sides

        # Total compaction area
        A_comp_total = A_comp_platform + A_comp_trench

        # --- Lifts and passes ---
        n_lifts_platform = 0
        if A_site > 0 and H_site > 0 and H_lift > 0:
            n_lifts_platform = math.ceil(H_site / H_lift)

        n_lifts_trench = 0
        if L_trench > 0 and W_trench > 0 and H_trench > 0 and H_lift > 0:
            n_lifts_trench = math.ceil(H_trench / H_lift)

        # Total area * passes
        A_pass_platform = A_comp_platform * n_lifts_platform * passes_per_lift
        A_pass_trench = A_comp_trench * n_lifts_trench * passes_per_lift
        A_pass_total = A_pass_platform + A_pass_trench

        # --- Costs ---
        cost_cut = V_cut_total * cost_per_m3_cut
        cost_compaction = A_pass_total * cost_per_m2_pass
        cost_total = cost_cut + cost_compaction

        # --- Update labels ---
        self.lbl_site_volume.setText(f"{V_site:,.3f} m³")
        self.lbl_trench_volume.setText(f"{V_trench:,.3f} m³")
        self.lbl_total_cut_volume.setText(f"{V_cut_total:,.3f} m³")

        self.lbl_platform_comp_area.setText(f"{A_comp_platform:,.2f} m²")
        self.lbl_trench_comp_area.setText(f"{A_comp_trench:,.2f} m²")
        self.lbl_total_comp_area.setText(f"{A_comp_total:,.2f} m²")

        self.lbl_lifts_platform.setText(str(n_lifts_platform))
        self.lbl_lifts_trench.setText(str(n_lifts_trench))
        self.lbl_total_area_passes.setText(f"{A_pass_total:,.2f} m²·passes")

        self.lbl_cut_cost.setText(f"${cost_cut:,.2f}")
        self.lbl_compaction_cost.setText(f"${cost_compaction:,.2f}")
        self.lbl_total_cost.setText(f"${cost_total:,.2f}")

    def _on_reset_clicked(self) -> None:
        """Reset all inputs and outputs to defaults."""

        # Platform
        self.site_area_spin.setValue(0.0)
        self.site_depth_spin.setValue(0.0)

        # Trenches
        self.trench_length_spin.setValue(0.0)
        self.trench_width_spin.setValue(0.0)
        self.trench_depth_spin.setValue(0.0)
        self.trench_count_spin.setValue(1)

        # Compaction
        self.compaction_target_spin.setValue(95.0)
        self.lift_thickness_spin.setValue(20.0)
        self.roller_width_spin.setValue(2.0)
        self.passes_per_lift_spin.setValue(4)

        # Costs
        self.cost_per_m3_cut_spin.setValue(3.0)
        self.cost_per_m2_pass_spin.setValue(0.01)

        # Results
        self.lbl_site_volume.setText("0.000 m³")
        self.lbl_trench_volume.setText("0.000 m³")
        self.lbl_total_cut_volume.setText("0.000 m³")
        self.lbl_platform_comp_area.setText("0.00 m²")
        self.lbl_trench_comp_area.setText("0.00 m²")
        self.lbl_total_comp_area.setText("0.00 m²")
        self.lbl_lifts_platform.setText("0")
        self.lbl_lifts_trench.setText("0")
        self.lbl_total_area_passes.setText("0.00 m²·passes")
        self.lbl_cut_cost.setText("$0.00")
        self.lbl_compaction_cost.setText("$0.00")
        self.lbl_total_cost.setText("$0.00")
