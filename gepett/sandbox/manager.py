import subprocess
import uuid
from pathlib import Path
from ..adapter.mc_adapter import MinecraftAdapter

class SandboxManager:
    """
    Manages the lifecycle of sandboxed environments, primarily by creating
    and loading world snapshots.
    """
    def __init__(self, adapter: MinecraftAdapter, scripts_dir: str, snapshots_dir: str):
        self.adapter = adapter
        self.scripts_dir = Path(scripts_dir)
        self.snapshots_dir = Path(snapshots_dir)

        if not self.scripts_dir.is_dir():
            raise FileNotFoundError(f"Scripts directory not found: {self.scripts_dir}")
        if not self.snapshots_dir.is_dir():
            # Create snapshot dir if it doesn't exist
            self.snapshots_dir.mkdir(parents=True, exist_ok=True)

    def snapshot(self, world_id: str = None) -> str:
        """
        Creates a snapshot of the current world by calling the snapshot_world.sh script.
        This is a host-level operation that copies the server's world files.

        Args:
            world_id: An optional ID for the snapshot. If None, a UUID is generated.

        Returns:
            The ID of the created snapshot.
        """
        snapshot_id = world_id or str(uuid.uuid4())
        script_path = self.scripts_dir / "snapshot_world.sh"

        print(f"[SandboxManager] Creating snapshot '{snapshot_id}'...")

        if not script_path.is_file():
            raise FileNotFoundError(f"Snapshot script not found: {script_path}")

        try:
            # The script is executed from the project root, so paths should be relative to that.
            # The script itself handles the relative paths to ../server and ../worlds_snapshots
            result = subprocess.run(
                [str(script_path), snapshot_id],
                capture_output=True,
                text=True,
                check=True,
                cwd=self.scripts_dir.parent # Run from project root
            )
            print(result.stdout)
            if result.stderr:
                print("Stderr:", result.stderr)
            print(f"[SandboxManager] Snapshot '{snapshot_id}' created successfully.")
            return snapshot_id
        except subprocess.CalledProcessError as e:
            print(f"!!! Failed to create snapshot '{snapshot_id}'.")
            print("Stdout:", e.stdout)
            print("Stderr:", e.stderr)
            raise RuntimeError(f"Snapshot script failed with exit code {e.returncode}") from e

    def load(self, world_id: str):
        """
        Requests the bot to trigger a world load on the server.
        This relies on a server-side plugin or mechanism that the bot can trigger.
        For the MVP, this sends a control command and assumes the bot handles it.

        Args:
            world_id: The ID of the snapshot to load.
        """
        snapshot_path = self.snapshots_dir / world_id
        if not snapshot_path.is_dir():
            raise FileNotFoundError(f"Snapshot '{world_id}' not found at {snapshot_path}")

        print(f"[SandboxManager] Requesting load of snapshot '{world_id}'...")
        try:
            response = self.adapter.control({"cmd": "load", "id": world_id})
            if response.get("ok"):
                print(f"[SandboxManager] Load command for '{world_id}' sent successfully.")
                # A real implementation would need to wait for the server/bot to restart and be ready.
            else:
                raise RuntimeError(f"Bot returned an error on load command: {response.get('error')}")
        except Exception as e:
            print(f"!!! Failed to send load command for snapshot '{world_id}'.")
            raise RuntimeError("Failed to execute load command via adapter.") from e

    def list_snapshots(self) -> list[str]:
        """Lists available snapshots."""
        if not self.snapshots_dir.exists():
            return []
        return [p.name for p in self.snapshots_dir.iterdir() if p.is_dir()]
