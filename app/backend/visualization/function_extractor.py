import ast
import os

PLOTS_PATH = os.path.join("app", "backend", "visualization", "plots.py")


def read_code_from_file(filepath: str) -> str:
    """Read the source code from the given file."""

    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()


def get_required_and_default_params(node: ast.FunctionDef):
    """Extract required parameters and default parameter names from a function node."""

    defaults_count = len(node.args.defaults)

    required_params = (
        node.args.args[:-defaults_count] if defaults_count > 0 else node.args.args
    )

    default_params = (
        [p.arg for p in node.args.args[-defaults_count:]] if defaults_count > 0 else []
    )

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

    dict_args_lines = ["{"]

    for param in required_params:

        param_name = param.arg
        type_hint = ast.unparse(param.annotation) if param.annotation else "Any"
        description = args_dict.get(param_name, "No description")

        dict_args_lines.append(
            f'    "{param_name}": None, # {type_hint}: {description}'
        )

    dict_args_lines.append("}")

    return "\n".join(dict_args_lines)


def extract_plot_functions():
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

    data = extract_plot_functions()

    with open("functions.txt", "w", encoding="utf-8") as f:
        f.write(repr(data))
