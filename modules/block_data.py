"""
block_data.py

Data definitions for breeze / hollow concrete blocks, pallet sizes,
and default approximate pricing for Saudi Arabia (converted to USD).

Notes
-----
- Prices are rough defaults based on online KSA retail listings for
  normal / hollow concrete blocks in the ~40x20x(10–20) cm range,
  typically around 2.0–2.5 SAR per piece :contentReference[oaicite:1]{index=1}
- 1 SAR ≈ 0.27 USD used here.
- User can override cost per block in the GUI at any time.
"""

from dataclasses import dataclass
from typing import Dict, List


@dataclass
class BlockType:
    """Represents a block size and commercial info."""
    name: str
    length_m: float        # length along the wall (m)
    height_m: float        # vertical dimension (m)
    thickness_m: float     # wall thickness (m) – not used yet but kept for future
    blocks_per_pallet: int
    default_cost_usd: float


# You can freely edit / expand this dict as needed.
BLOCK_TYPES: Dict[str, BlockType] = {
    # --------------------------------------------------------
    # Standard Hollow Blocks (Saudi Arabia common sizes)
    # --------------------------------------------------------
    "40 x 20 x 20 cm (hollow)": BlockType(
        name="40 x 20 x 20 cm (hollow)",
        length_m=0.40,
        height_m=0.20,
        thickness_m=0.20,
        blocks_per_pallet=108,
        default_cost_usd=0.55,
    ),
    "40 x 20 x 15 cm (hollow)": BlockType(
        name="40 x 20 x 15 cm (hollow)",
        length_m=0.40,
        height_m=0.20,
        thickness_m=0.15,
        blocks_per_pallet=120,
        default_cost_usd=0.50,
    ),
    "40 x 20 x 10 cm (hollow)": BlockType(
        name="40 x 20 x 10 cm (hollow)",
        length_m=0.40,
        height_m=0.20,
        thickness_m=0.10,
        blocks_per_pallet=150,
        default_cost_usd=0.45,
    ),

    # --------------------------------------------------------
    # Larger / smaller face dimensions (face area differs)
    # --------------------------------------------------------
    "30 x 20 x 20 cm (hollow)": BlockType(
        name="30 x 20 x 20 cm (hollow)",
        length_m=0.30,
        height_m=0.20,
        thickness_m=0.20,
        blocks_per_pallet=144,
        default_cost_usd=0.48,
    ),
    "20 x 20 x 20 cm (hollow)": BlockType(
        name="20 x 20 x 20 cm (hollow)",
        length_m=0.20,
        height_m=0.20,
        thickness_m=0.20,
        blocks_per_pallet=216,
        default_cost_usd=0.40,
    ),
    "50 x 20 x 20 cm (hollow)": BlockType(
        name="50 x 20 x 20 cm (hollow)",
        length_m=0.50,
        height_m=0.20,
        thickness_m=0.20,
        blocks_per_pallet=86,
        default_cost_usd=0.70,
    ),

    # --------------------------------------------------------
    # Solid Blocks (heavier, more expensive, different coverage)
    # --------------------------------------------------------
    "40 x 20 x 20 cm (solid)": BlockType(
        name="40 x 20 x 20 cm (solid)",
        length_m=0.40,
        height_m=0.20,
        thickness_m=0.20,
        blocks_per_pallet=96,
        default_cost_usd=0.85,
    ),
    "30 x 20 x 20 cm (solid)": BlockType(
        name="30 x 20 x 20 cm (solid)",
        length_m=0.30,
        height_m=0.20,
        thickness_m=0.20,
        blocks_per_pallet=128,
        default_cost_usd=0.75,
    ),

    # --------------------------------------------------------
    # Lightweight partition blocks (AAC / aerated)
    # --------------------------------------------------------
    "AAC 60 x 20 x 20 cm": BlockType(
        name="AAC 60 x 20 x 20 cm",
        length_m=0.60,
        height_m=0.20,
        thickness_m=0.20,
        blocks_per_pallet=72,
        default_cost_usd=1.60,
    ),
    "AAC 60 x 25 x 20 cm": BlockType(
        name="AAC 60 x 25 x 20 cm",
        length_m=0.60,
        height_m=0.25,
        thickness_m=0.20,
        blocks_per_pallet=60,
        default_cost_usd=1.90,
    ),
}

# BLOCK_TYPES: Dict[str, BlockType] = {
#     "40 x 20 x 20 cm (hollow)":
#         BlockType(
#             name="40 x 20 x 20 cm (hollow)",
#             length_m=0.40,
#             height_m=0.20,
#             thickness_m=0.20,
#             blocks_per_pallet=108,   # e.g. 18 per layer * 6 layers for 40x20x20 cm :contentReference[oaicite:2]{index=2}
#             default_cost_usd=0.55,   # ~2.0 SAR
#         ),
#     "40 x 20 x 15 cm (hollow)":
#         BlockType(
#             name="40 x 20 x 15 cm (hollow)",
#             length_m=0.40,
#             height_m=0.20,
#             thickness_m=0.15,
#             blocks_per_pallet=120,
#             default_cost_usd=0.50,   # slightly cheaper than 20 cm thick
#         ),
#     "40 x 20 x 10 cm (hollow)":
#         BlockType(
#             name="40 x 20 x 10 cm (hollow)",
#             length_m=0.40,
#             height_m=0.20,
#             thickness_m=0.10,
#             blocks_per_pallet=150,
#             default_cost_usd=0.45,
#         ),
# }


def get_block_names() -> List[str]:
    """
    Return the list of available block type names
    in a stable order for use in drop-downs.
    """
    return list(BLOCK_TYPES.keys())


def get_block_type(name: str) -> BlockType:
    """
    Safely retrieve a BlockType by name.
    Raises KeyError if not found.
    """
    return BLOCK_TYPES[name]
