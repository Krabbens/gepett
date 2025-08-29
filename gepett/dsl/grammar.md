# UniPlan DSL Grammar (EBNF)

This document defines the formal grammar for the Universal Planner (UniPlan) Domain-Specific Language. The language is used to create high-level, interpretable plans for the agent.

## Grammar Definition

```ebnf
program    ::= block
block      ::= "SEQUENCE" "{" stmt* "}" | stmt
stmt       ::= call_skill | prim | if_stmt | while_loop | ret_stmt
call_skill ::= "CALL_SKILL" "(" string "," json_args ")" ";"
prim       ::= "PRIM" "(" string "," json_args ")" ";"
if_stmt    ::= "IF" "(" condition ")" "{" stmt* "}" ( "ELSE" "{" stmt* "}" )?
while_loop ::= "WHILE" "(" condition "," "max_iters" "=" integer ")" "{" stmt* "}"
ret_stmt   ::= "RETURN" "(" json_expr ")" ";"

condition  ::= predicate  (* e.g., "inventory.iron_ore >= 10" *)
predicate  ::= string     (* For MVP, treated as an opaque string evaluated by the oracle *)

json_args  ::= json_object (* A valid JSON object as a string *)
json_expr  ::= json_object (* A valid JSON object as a string *)

string     ::= /"[^"]*"/
integer    ::= /[0-9]+/
json_object::= /{.*}/

WHITESPACE ::= (" " | "\t" | "\n" | "\r")+
%ignore WHITESPACE
```

## Description of Components

- **program**: The root of a UniPlan script. It's a single block of statements.
- **block**: A collection of statements. Can be a single statement or a sequence of statements enclosed in `SEQUENCE { ... }`.
- **stmt**: A single instruction or control flow structure.
- **CALL_SKILL**: Invokes a high-level, learned, or pre-programmed skill. The skill's implementation is located elsewhere (e.g., a Python script).
  - `string`: The name of the skill to call.
  - `json_args`: A JSON object containing the parameters for the skill.
- **PRIM**: Executes a primitive action, which corresponds directly to a `PrimitiveAction` sent to the bot.
  - `string`: The name of the primitive action (e.g., "move", "dig").
  - `json_args`: A JSON object containing the parameters for the action.
- **IF**: Conditional execution. The `condition` is evaluated by the Intrinsic Oracle.
- **WHILE**: A loop that executes as long as a `condition` is true, with a safeguard `max_iters` to prevent infinite loops.
- **RETURN**: Exits the plan and returns a JSON object, typically indicating success or failure and final results.
- **condition**: An expression that evaluates to true or false. In the initial implementation, this is an opaque string passed to the Intrinsic Oracle for evaluation against the current `StateFrame`.

## Example

```
SEQUENCE {
  CALL_SKILL("LocateResource", {"type":"iron_ore","radius":30});
  WHILE("inventory.iron_ore < 10", max_iters=20) {
    CALL_SKILL("GatherUntil", {"item":"iron_ore","count":1,"timeout":60});
  }
  IF ("inventory.iron_ore >= 10") {
    PRIM("CRAFT", {"recipe":"furnace"});
    RETURN({"success": true, "message": "Furnace crafted."});
  } ELSE {
    RETURN({"success": false, "message": "Failed to gather enough iron ore."});
  }
}
```
