import time
from .parser import ASTNode, SequenceNode, CallSkillNode, PrimNode, IfNode, WhileNode, ReturnNode, parse_uniplan
from ..adapter.mc_adapter import MinecraftAdapter
from ..adapter.schemas import PrimitiveAction, StateFrame

# --- Mock/Placeholder Dependencies ---
# These will be replaced by actual components later.

class MockOracle:
    """A mock Intrinsic Oracle to evaluate conditions."""
    def evaluate(self, condition: str, state: StateFrame) -> bool:
        print(f"  [Oracle] Evaluating condition: '{condition}'")
        try:
            # WARNING: This is a simplified and unsafe evaluator for MVP.
            # A real implementation would use a safe, sandboxed expression evaluator.
            if "inventory.iron_ore" in condition:
                iron_ore = next((item.count for item in state.inventory if item.id == 'iron_ore'), 0)
                # This is still unsafe, but demonstrates the principle.
                return eval(condition, {"inventory.iron_ore": iron_ore})
        except Exception as e:
            print(f"  [Oracle] Failed to evaluate condition '{condition}': {e}")
            return False
        print(f"  [Oracle] Condition '{condition}' is False")
        return False

def mock_skill_gather(interpreter, context, params):
    """A mock implementation of a skill as a Python function."""
    print(f"  [Skill] Running mock skill 'GatherUntil' with params: {params}")
    # This is where a more complex loop of PRIMs would go.
    # For MVP, we just simulate it by sending one dig command.
    action = PrimitiveAction(name="dig", params={"x": 1, "y": 1, "z": 1}) # Dummy coords
    context['current_state'] = interpreter.adapter.step(action)
    context['trace'].append((context['current_state'], action))
    print("  [Skill] Mock skill 'GatherUntil' finished.")
    return context

mock_skill_registry = {
    "GatherUntil": mock_skill_gather
}

# --- Interpreter ---

class UniPlanInterpreter:
    def __init__(self, adapter: MinecraftAdapter, oracle, skill_registry):
        self.adapter = adapter
        self.oracle = oracle
        self.skill_registry = skill_registry
        self.dispatch_table = {
            SequenceNode: self._visit_sequence,
            PrimNode: self._visit_prim,
            CallSkillNode: self._visit_call_skill,
            IfNode: self._visit_if,
            WhileNode: self._visit_while,
            ReturnNode: self._visit_return,
        }

    def execute(self, plan_text: str, initial_state: StateFrame):
        """Parses and executes a UniPlan script."""
        print(f"[Interpreter] Executing plan...")
        ast = parse_uniplan(plan_text)

        context = {
            "current_state": initial_state,
            "trace": [],
            "return_value": None,
            "done": False
        }

        self._visit(ast, context)

        print(f"[Interpreter] Execution finished. Return value: {context['return_value']}")
        return context

    def _visit(self, node: ASTNode, context: dict):
        if context['done']:
            return

        visitor = self.dispatch_table.get(type(node))
        if not visitor:
            raise ValueError(f"No visitor method for AST node type: {type(node)}")

        visitor(node, context)

    def _visit_sequence(self, node: SequenceNode, context: dict):
        for stmt in node.statements:
            self._visit(stmt, context)
            if context['done']:
                break

    def _visit_prim(self, node: PrimNode, context: dict):
        print(f"  [Prim] Executing: {node.name} with {node.args}")
        action = PrimitiveAction(name=node.name, params=node.args)
        new_state = self.adapter.step(action)
        context['current_state'] = new_state
        context['trace'].append((new_state, action))
        time.sleep(0.5) # Small delay to make execution observable

    def _visit_call_skill(self, node: CallSkillNode, context: dict):
        print(f"  [Skill] Calling: {node.name} with {node.args}")
        skill_func = self.skill_registry.get(node.name)
        if not skill_func:
            raise ValueError(f"Skill '{node.name}' not found in registry.")

        # The skill function is responsible for updating the context
        context = skill_func(self, context, node.args)

    def _visit_if(self, node: IfNode, context: dict):
        if self.oracle.evaluate(node.condition, context['current_state']):
            self._visit(node.true_block, context)
        elif node.false_block:
            self._visit(node.false_block, context)

    def _visit_while(self, node: WhileNode, context: dict):
        iters = 0
        while iters < node.max_iters and not context['done']:
            if not self.oracle.evaluate(node.condition, context['current_state']):
                break
            self._visit(node.loop_block, context)
            iters += 1
        if iters == node.max_iters:
            print(f"  [While] Loop reached max_iters ({node.max_iters}).")

    def _visit_return(self, node: ReturnNode, context: dict):
        print(f"  [Return] Reached RETURN with value: {node.value}")
        context['return_value'] = node.value
        context['done'] = True


if __name__ == '__main__':
    # This is a placeholder for a proper test.
    # It cannot run standalone without a running adapter and bot.
    print("UniPlan Interpreter. To test, run a full e2e smoke test.")

    example_plan_for_test = """
    SEQUENCE {
      CALL_SKILL("GatherUntil", {"item":"iron_ore","count":1});
      PRIM("JUMP", {});
      RETURN({"success": "true"});
    }
    """

    print("\nExample plan to be executed:")
    print(example_plan_for_test)

    # To run this, you would need to set up the adapter:
    # config = ...
    # adapter = MinecraftAdapter(config)
    # adapter.connect()
    # initial_state = adapter.receive_state()
    # oracle = MockOracle()
    # interpreter = UniPlanInterpreter(adapter, oracle, mock_skill_registry)
    # result_context = interpreter.execute(example_plan_for_test, initial_state)
    # adapter.close()
