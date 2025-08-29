import time
from .manager import SandboxManager
from ..dsl.interpreter import UniPlanInterpreter, MockOracle, mock_skill_registry
from ..adapter.mc_adapter import MinecraftAdapter

class PlanExecutor:
    """
    Orchestrates the execution of a UniPlan within a sandboxed environment.
    It uses a SandboxManager to prepare the environment and a UniPlanInterpreter
    to run the plan.
    """
    def __init__(self, adapter: MinecraftAdapter, config: dict):
        self.adapter = adapter
        self.config = config

        # In a real scenario, these would be properly instantiated objects.
        # For MVP, we use the mock implementations.
        self.oracle = MockOracle()
        self.skill_registry = mock_skill_registry

        self.interpreter = UniPlanInterpreter(
            adapter=self.adapter,
            oracle=self.oracle,
            skill_registry=self.skill_registry
        )

        self.sandbox_manager = SandboxManager(
            adapter=self.adapter,
            scripts_dir=self.config['sandbox']['scripts_dir'],
            snapshots_dir=self.config['sandbox']['snapshots_dir']
        )

    def run_in_sandbox(self, plan_text: str, world_snapshot_id: str):
        """
        Executes a plan in a sandboxed environment.

        The process is:
        1. Load a world snapshot to ensure a clean state.
        2. Wait for the environment to be ready.
        3. Execute the plan using the interpreter.
        4. Return the results.

        Args:
            plan_text: The UniPlan script to execute.
            world_snapshot_id: The ID of the world snapshot to load.

        Returns:
            The final context dictionary from the interpreter.
        """
        print(f"\n--- Starting Plan Execution in Sandbox (Snapshot: {world_snapshot_id}) ---")

        # 1. Load the snapshot
        try:
            self.sandbox_manager.load(world_snapshot_id)
            print("[Executor] Load command sent. Waiting for environment to be ready...")
            # This is a critical and complex step. A true implementation requires
            # robust health checking of the server and bot after a world load,
            # which likely involves a restart.
            # For MVP, we'll just wait a fixed amount of time and assume it worked.
            time.sleep(15) # Generous wait for server/bot to restart
            print("[Executor] Assumed environment is ready.")
        except (FileNotFoundError, RuntimeError) as e:
            print(f"!!! Halting execution due to sandbox error: {e}")
            return {"error": str(e)}

        # 2. Get initial state
        print("[Executor] Acquiring initial state from the environment...")
        initial_state = self.adapter.receive_state(block=True)
        if not initial_state:
            print("!!! Failed to get initial state after loading snapshot. Halting.")
            return {"error": "Failed to get initial state."}
        print("[Executor] Initial state acquired.")

        # 3. Execute the plan
        results = self.interpreter.execute(plan_text, initial_state)

        print("--- Plan Execution Finished ---")
        return results

if __name__ == '__main__':
    # This is a placeholder for a proper test.
    # It requires a full running environment.
    print("Plan Executor. To test, run a full e2e smoke test.")

    # Example of how it would be used:
    # config = ... # load from yaml
    # adapter = MinecraftAdapter(config['adapter'])
    # adapter.connect()
    #
    # executor = PlanExecutor(adapter, config)
    #
    # # First, ensure a snapshot exists
    # manager = SandboxManager(adapter, config['sandbox']['scripts_dir'], config['sandbox']['snapshots_dir'])
    # if "base_world" not in manager.list_snapshots():
    #     print("Creating initial 'base_world' snapshot...")
    #     manager.snapshot("base_world")
    #
    # plan = 'PRIM("JUMP", {});'
    # result_context = executor.run_in_sandbox(plan, "base_world")
    #
    # print("\nExecution Result Context:")
    # print(result_context)
    #
    # adapter.close()
