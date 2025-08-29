import json
from lark import Lark, Transformer, v_args
from dataclasses import dataclass
from typing import List, Dict, Any, Optional

# --- AST Node Definitions ---
# We use dataclasses to represent the nodes of our Abstract Syntax Tree.

@dataclass
class ASTNode:
    pass

@dataclass
class SequenceNode(ASTNode):
    statements: List[ASTNode]

@dataclass
class CallSkillNode(ASTNode):
    name: str
    args: Dict[str, Any]

@dataclass
class PrimNode(ASTNode):
    name: str
    args: Dict[str, Any]

@dataclass
class IfNode(ASTNode):
    condition: str
    true_block: SequenceNode
    false_block: Optional[SequenceNode] = None

@dataclass
class WhileNode(ASTNode):
    condition: str
    max_iters: int
    loop_block: SequenceNode

@dataclass
class ReturnNode(ASTNode):
    value: Dict[str, Any]

# --- Grammar Definition ---
# The grammar is based on the one defined in dsl/grammar.md.

uniplan_grammar = r"""
    ?program: block

    ?block: "SEQUENCE" "{" statement* "}" -> sequence
          | statement

    ?statement: call_skill
              | prim
              | if_stmt
              | while_loop
              | ret_stmt

    call_skill: "CALL_SKILL" "(" ESCAPED_STRING "," json_args ")" ";"
    prim: "PRIM" "(" ESCAPED_STRING "," json_args ")" ";"
    if_stmt: "IF" "(" condition ")" "{" statement* "}" ("ELSE" "{" statement* "}")? -> if_statement
    while_loop: "WHILE" "(" condition "," "max_iters" "=" INT ")" "{" statement* "}" -> while_statement
    ret_stmt: "RETURN" "(" json_expr ")" ";"

    ?condition: ESCAPED_STRING
    ?json_args: json_object
    ?json_expr: json_object

    json_object: "{}" | "{" json_members "}"
    json_members: json_pair ("," json_pair)*
    json_pair: ESCAPED_STRING ":" json_value
    ?json_value: ESCAPED_STRING | SIGNED_NUMBER | "true" | "false" | "null" | json_object | json_array
    json_array: "[]" | "[" json_value ("," json_value)* "]"

    %import common.ESCAPED_STRING
    %import common.SIGNED_NUMBER
    %import common.INT
    %import common.WS
    %ignore WS
"""

# --- Transformer ---
# This class walks the parse tree created by Lark and transforms it into our AST.

@v_args(inline=True) # Makes the transformer methods receive children directly
class AstTransformer(Transformer):
    def ESCAPED_STRING(self, s):
        # Remove quotes
        return s[1:-1]

    def INT(self, i):
        return int(i)

    def json_object(self, *items):
        return dict(items)

    def json_array(self, *items):
        return list(items)

    def json_pair(self, key, value):
        return key, value

    # Handle primitive JSON values
    def SIGNED_NUMBER(self, n):
        return float(n)

    def "true"(self, _):
        return True

    def "false"(self, _):
        return False

    def "null"(self, _):
        return None

    def json_args(self, args):
        return args

    def json_expr(self, expr):
        return expr

    def sequence(self, *statements):
        return SequenceNode(statements=list(statements))

    def call_skill(self, name, args):
        return CallSkillNode(name=name, args=args)

    def prim(self, name, args):
        return PrimNode(name=name, args=args)

    def if_statement(self, condition, true_block, false_block=None):
        true_sequence = SequenceNode(statements=list(true_block.children))
        false_sequence = None
        if false_block:
            false_sequence = SequenceNode(statements=list(false_block.children))
        return IfNode(condition=condition, true_block=true_sequence, false_block=false_sequence)

    def while_statement(self, condition, max_iters, *statements):
        loop_sequence = SequenceNode(statements=list(statements))
        return WhileNode(condition=condition, max_iters=max_iters, loop_block=loop_sequence)

    def ret_stmt(self, value):
        return ReturnNode(value=value)

    def program(self, block):
        # If the program is a single statement, wrap it in a sequence
        if not isinstance(block, SequenceNode):
            return SequenceNode(statements=[block])
        return block


# --- Parser Singleton ---

uniplan_parser = Lark(uniplan_grammar, start='program', parser='lalr', transformer=AstTransformer())

def parse_uniplan(text: str) -> ASTNode:
    """

    Parses a UniPlan script and returns the root of the AST.
    """
    return uniplan_parser.parse(text)

# --- Example Usage ---

if __name__ == '__main__':
    example_plan = """
    SEQUENCE {
      CALL_SKILL("GatherUntil", {"item":"iron_ore","count":10,"timeout":180});
      IF ("inventory.iron_ore >= 10") {
        PRIM("CRAFT", {"recipe":"furnace"});
      } ELSE {
        CALL_SKILL("ReportFailure", {"reason": "Could not find iron."});
      }
      WHILE("furnace.not_placed", max_iters=5) {
          CALL_SKILL("PlaceNear", {"structure":"base","item":"furnace"});
      }
      RETURN({"success": "true"});
    }
    """

    print("--- Parsing Example UniPlan ---")
    print(example_plan)

    try:
        ast = parse_uniplan(example_plan)
        print("\n--- Generated AST ---")
        import pprint
        pprint.pprint(ast)

        # Test single statement
        ast_single = parse_uniplan('PRIM("JUMP", {});')
        print("\n--- Single Statement AST ---")
        pprint.pprint(ast_single)

    except Exception as e:
        print(f"\n--- Parsing Failed ---")
        print(e)
