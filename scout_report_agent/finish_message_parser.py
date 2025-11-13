"""
Parser for extracting scout report data from Gemini's malformed function call messages.

Gemini sometimes generates Python-like code instead of proper JSON when calling
submit_scout_report. This parser extracts the structured data from that format.
"""

import ast
import re
from typing import Dict, Any, Optional


def parse_finish_message(finish_message: str) -> Optional[Dict[str, Any]]:
    """
    Parse a finish_message that contains Python-like function call code.

    Example input:
        "Malformed function call: print(default_api.submit_scout_report(
            player=default_api.SubmitScoutReportPlayer(
                name='Bryce Underwood',
                physicals={'Height': '6ft 4in'},
                socials={'Twitter': '@handle'}
            ),
            tags=['Football', 'Quarterback'],
            ...
        ))"

    Returns:
        dict with the scout report data, or None if parsing fails
    """
    try:
        # Extract the Python code from the message
        # Format: "Malformed function call: print(default_api.submit_scout_report(...data...))"
        if "submit_scout_report(" not in finish_message:
            return None

        # Find the start of the function call
        start_idx = finish_message.find("submit_scout_report(")
        if start_idx == -1:
            return None

        # Extract everything from "submit_scout_report(" to the end
        code_snippet = finish_message[start_idx:]

        # Find the matching closing parenthesis
        # We need to count parentheses to find the right one
        paren_count = 0
        end_idx = -1
        for i, char in enumerate(code_snippet):
            if char == '(':
                paren_count += 1
            elif char == ')':
                paren_count -= 1
                if paren_count == 0:
                    end_idx = i + 1
                    break

        if end_idx == -1:
            return None

        # Get the full function call
        func_call = code_snippet[:end_idx]

        # Wrap it in a way we can parse with AST
        # Replace the custom class constructors with dict constructors
        clean_code = func_call
        clean_code = re.sub(r'default_api\.SubmitScoutReportPlayer\(', 'dict(', clean_code)
        clean_code = re.sub(r'default_api\.SubmitScoutReportAnalysis\(', 'dict(', clean_code)

        # Parse as a function call expression
        # Wrap it to make it valid Python: "result = submit_scout_report(...)"
        full_code = f"result = {clean_code}"

        # Parse the AST
        tree = ast.parse(full_code)

        # Extract the Call node
        assign_node = tree.body[0]
        if not isinstance(assign_node, ast.Assign):
            return None

        call_node = assign_node.value
        if not isinstance(call_node, ast.Call):
            return None

        # Extract the arguments
        scout_report = {}

        # Process keyword arguments
        for keyword in call_node.keywords:
            arg_name = keyword.arg
            arg_value = _eval_ast_node(keyword.value)
            scout_report[arg_name] = arg_value

        return {"status": "success", "scout_report": scout_report}

    except Exception as e:
        print(f"Error parsing finish_message: {e}")
        return None


def _eval_ast_node(node):
    """
    Safely evaluate an AST node to extract its Python value.
    """
    if isinstance(node, ast.Constant):
        return node.value
    elif isinstance(node, ast.Str):  # Python 3.7 compatibility
        return node.s
    elif isinstance(node, ast.Num):  # Python 3.7 compatibility
        return node.n
    elif isinstance(node, ast.List):
        return [_eval_ast_node(item) for item in node.elts]
    elif isinstance(node, ast.Tuple):
        return tuple(_eval_ast_node(item) for item in node.elts)
    elif isinstance(node, ast.Dict):
        return {
            _eval_ast_node(k): _eval_ast_node(v)
            for k, v in zip(node.keys, node.values)
        }
    elif isinstance(node, ast.Call):
        # This handles dict(...) calls
        if isinstance(node.func, ast.Name) and node.func.id == 'dict':
            result = {}
            for keyword in node.keywords:
                result[keyword.arg] = _eval_ast_node(keyword.value)
            return result
        else:
            raise ValueError(f"Unsupported function call: {ast.dump(node)}")
    elif isinstance(node, ast.UnaryOp):
        operand = _eval_ast_node(node.operand)
        if isinstance(node.op, ast.USub):
            return -operand
        elif isinstance(node.op, ast.UAdd):
            return +operand
    else:
        raise ValueError(f"Unsupported AST node type: {type(node).__name__}")


# Test the parser with the actual data
if __name__ == "__main__":
    import tempfile
    import os

    # Read the saved finish_message
    temp_file = os.path.join(tempfile.gettempdir(), "scout_report_finish_message.txt")
    if os.path.exists(temp_file):
        with open(temp_file, 'r') as f:
            finish_message = f.read()

        print("Parsing finish_message...")
        result = parse_finish_message(finish_message)

        if result:
            print("\n✅ Successfully parsed!")
            print("\nExtracted data:")
            import json
            print(json.dumps(result, indent=2))
        else:
            print("\n❌ Failed to parse")
    else:
        print(f"Temp file not found: {temp_file}")
