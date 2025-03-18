"""
This script extracts detailed information about plot functions defined in the plots.py file.

It parses the source code to retrieve each function's:
- signature
- docstring
- parameter details
cleaning and organizing these elements into a structured list.

In plain English,

the module reads
the plotting functions' source code,
extracts metadata about
how each plot is configured,
and outputs this information
so that other components can easily use it
for automated visualization generation.
"""

# Python
import ast
import os

PLOTS_PATH = os.path.join("app", "backend", "visualization", "plots.py")


def retrieve_plot_function_details():
    """Extract functions information from the plots file."""

    code = read_code_from_file(PLOTS_PATH)
    functions = []
    abstract_syntax_tree = ast.parse(code)

    for node in ast.iter_child_nodes(abstract_syntax_tree):

        if isinstance(node, ast.FunctionDef):

            func_info = {
                "name": node.name,
                "interface": "",
                "description": "",
                "dict_args": "",
            }

            required_params, default_params = get_required_and_default_params(node)
            docstring = extract_docstring(node)

            func_info["interface"] = build_interface(node, required_params)
            func_info["description"] = clean_docstring(docstring, default_params)
            func_info["dict_args"] = build_dict_args(docstring, required_params)

            functions.append(func_info)

    return functions


def read_code_from_file(filepath: str) -> str:
    """Read the source code from the given file."""

    with open(filepath, "r", encoding="utf-8") as _file:
        return _file.read()


def get_required_and_default_params(node: ast.FunctionDef):
    """Extracts required and default parameters from a function definition node.

    Required parameters are those without defaults in the signature or body assignments.
    Default parameters are those explicitly set in the function signature.
    """
    parameters = node.args.args
    num_signature_defaults = len(node.args.defaults)

    # Determine parameters with defaults in the function signature
    signature_defaults = (
        {param.arg for param in parameters[-num_signature_defaults:]}
        if num_signature_defaults > 0
        else set()
    )

    # Helper to check if a value node represents None
    def is_none(value_node):
        return (isinstance(value_node, ast.Constant) and value_node.value is None) or (
            hasattr(ast, "Constant")
            and isinstance(value_node, ast.Constant)
            and value_node.value is None
        )

    body_defaults = set()
    if num_signature_defaults > 0:
        param_names = {param.arg for param in parameters}
        for stmt in node.body:
            # Check for simple assignments (e.g., `param = None`)
            if not (isinstance(stmt, ast.Assign) and len(stmt.targets) == 1):
                continue

            target = stmt.targets[0]
            if not isinstance(target, ast.Name):
                continue

            param_name = target.id
            # Skip non-parameters or parameters with existing signature defaults
            if param_name not in param_names or param_name in signature_defaults:
                continue

            if is_none(stmt.value):
                body_defaults.add(param_name)

    # Combine defaults from signature and body
    all_defaults = signature_defaults.union(body_defaults)
    required_params = [param for param in parameters if param.arg not in all_defaults]
    # Default parameters retain their original order from the signature
    default_params = [
        param.arg for param in parameters if param.arg in signature_defaults
    ]

    return required_params, default_params


def build_interface(node: ast.FunctionDef, required_params: list) -> str:
    """Build the function interface line with required parameters only."""

    param_strings = []

    for param in required_params:

        param_name = param.arg

        # If a type annotation exists, include it
        type_hint = ast.unparse(param.annotation) if param.annotation else ""
        param_str = f"{param_name}: {type_hint}" if type_hint else param_name
        param_strings.append(param_str)

    return f"def {node.name}({', '.join(param_strings)}):"


def extract_docstring(node: ast.FunctionDef) -> str:
    """Extract the docstring from a function node."""

    if node.body and isinstance(node.body[0], ast.Expr):

        docstring_node = node.body[0]

        if isinstance(docstring_node.value, ast.Constant):
            return docstring_node.value.value

    return ""


def clean_docstring(docstring: str, default_params: list) -> str:
    """Process docstring to remove default parameters from Args and exclude Returns."""

    cleaned_doc_lines = []
    in_args_section = False
    skip_remaining = False  # Flag to skip lines after Returns

    for line in docstring.split("\n"):

        if skip_remaining:
            continue

        stripped_line = line.strip()

        # Check for the start of the Args section
        if stripped_line.lower().startswith("args:"):
            in_args_section = True
            cleaned_doc_lines.append(line)
            continue

        if in_args_section:

            # End of Args section if an empty line or another section is encountered
            if not stripped_line or stripped_line.lower().startswith(
                ("returns:", "return:", "raises:", "example:")
            ):
                in_args_section = False

                if stripped_line.lower().startswith(("returns:", "return:")):
                    skip_remaining = True
                    continue

            else:

                # Skip the line if it is a default parameter line
                if ":" in stripped_line:

                    param_part = stripped_line.split(":", 1)[0].strip()
                    if param_part in default_params:
                        continue

        if not skip_remaining:
            cleaned_doc_lines.append(line)

    return "\n".join(cleaned_doc_lines).strip()


def build_dict_args(docstring: str, required_params: list) -> str:
    """Build a dictionary of required parameters with type hints and descriptions."""

    args_dict = parse_args_from_docstring(docstring)

    dict_args = {}

    for param in required_params:

        param_name = param.arg
        type_hint = ast.unparse(param.annotation) if param.annotation else "Any"

        description = args_dict.get(param_name, "No description")

        dict_args[param_name] = {
            "type": type_hint,
            "description": description,
        }

    return dict_args


def parse_args_from_docstring(docstring: str) -> dict:
    """Extract parameter descriptions from the docstring's Args section."""

    args_dict = {}

    if not docstring:
        return args_dict

    in_args = False

    for line in docstring.split("\n"):

        line = line.strip()

        if line.lower().startswith("args:"):
            in_args = True
            continue

        if in_args:

            if not line or line.lower().startswith(
                ("return:", "returns:", "raises:", "example:")
            ):
                break  # End of Args section

            if ":" in line:

                param, desc = line.split(":", 1)
                args_dict[param.strip()] = desc.strip()

    return args_dict


if __name__ == "__main__":

    data = retrieve_plot_function_details()

    with open("functions.txt", "w", encoding="utf-8") as f:
        f.write(repr(data))
