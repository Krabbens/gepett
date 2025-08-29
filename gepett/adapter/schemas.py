import json
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Tuple

# --- Nested Dataclasses for StateFrame ---

@dataclass
class Position:
    x: float
    y: float
    z: float
    yaw: float
    pitch: float

@dataclass
class InventoryItem:
    id: str
    count: int

@dataclass
class NearbyBlocks:
    grid_origin: Tuple[int, int, int]
    size: Tuple[int, int, int]
    blocks: List[List[List[int]]] # 3D grid of block IDs

@dataclass
class Entity:
    id: str
    kind: str
    pos: Tuple[float, float, float]

@dataclass
class Metrics:
    health: int
    hunger: int
    time: int
    light: int

@dataclass
class ActionSchema:
    name: str
    params: Dict[str, str] # e.g., {"x": "float", "y": "float"}

# --- Main StateFrame Dataclass ---

@dataclass
class StateFrame:
    """
    Represents a snapshot of the agent's state in the environment.
    This structure is sent from the Node.js bot to the Python core.
    """
    visual: Optional[bytes]
    position: Position
    inventory: List[InventoryItem]
    nearby_blocks: NearbyBlocks
    entities: List[Entity]
    metrics: Metrics
    available_actions_schema: List[ActionSchema]

# --- Action Dataclass ---

@dataclass
class PrimitiveAction:
    """
    Represents a single low-level action to be executed by the bot.
    This structure is sent from the Python core to the Node.js bot.
    """
    name: str
    params: Dict[str, Any] = field(default_factory=dict)


# --- Example Data ---

def examples():
    """Returns example instances of the schemas for testing and documentation."""

    example_state = StateFrame(
        visual=None,
        position=Position(x=10.5, y=64.0, z=-20.1, yaw=1.57, pitch=0.0),
        inventory=[InventoryItem(id="dirt", count=64), InventoryItem(id="stone_pickaxe", count=1)],
        nearby_blocks=NearbyBlocks(
            grid_origin=(5, 60, -25),
            size=(11, 11, 11),
            blocks=[[[0]*11]*11]*11 # Placeholder 11x11x11 grid of 'air'
        ),
        entities=[Entity(id="sheep_1", kind="sheep", pos=(15.0, 64.0, -22.0))],
        metrics=Metrics(health=20, hunger=20, time=6000, light=15),
        available_actions_schema=[
            ActionSchema(name="move", params={"x": "float", "y": "float", "z": "float"}),
            ActionSchema(name="dig", params={"x": "int", "y": "int", "z": "int"}),
        ]
    )

    example_action = PrimitiveAction(
        name="move",
        params={"x": 11.0, "y": 64.0, "z": -21.0}
    )

    return {
        "state_frame": example_state,
        "primitive_action": example_action,
        "state_frame_json": json.dumps(example_state, default=lambda o: o.__dict__, indent=2),
        "primitive_action_json": json.dumps(example_action, default=lambda o: o.__dict__, indent=2)
    }

if __name__ == '__main__':
    # Print examples when run as a script
    ex = examples()
    print("--- Example StateFrame ---")
    print(ex["state_frame"])
    print("\n--- Example PrimitiveAction ---")
    print(ex["primitive_action"])
    print("\n--- Example StateFrame (JSON) ---")
    print(ex["state_frame_json"])
    print("\n--- Example PrimitiveAction (JSON) ---")
    print(ex["primitive_action_json"])
