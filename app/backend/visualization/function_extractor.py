import ast
import os

PLOTS_PATH = os.path.join("app", "backend", "visualization", "plots.py")


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
            if not line or line.startswith(("returns:", "raises:", "example:")):
                break  # End of Args section
            if ":" in line:
                param, desc = line.split(":", 1)
                args_dict[param.strip()] = desc.strip()
    return args_dict


def extract_plot_functions():

    with open(PLOTS_PATH, "r", encoding="utf-8") as f:
        code = f.read()

    functions = []
    tree = ast.parse(code)

    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.FunctionDef):
            func_info = {
                "name": node.name,
                "interface": "",
                "description": "",
                "dict_args": "",
            }

            # Extract parameters and defaults
            defaults_count = len(node.args.defaults)
            required_params = (
                node.args.args[:-defaults_count]
                if defaults_count > 0
                else node.args.args
            )
            default_params = (
                [p.arg for p in node.args.args[-defaults_count:]]
                if defaults_count > 0
                else []
            )

            # Build interface without default parameters
            param_strings = []
            for param in required_params:
                param_name = param.arg
                type_hint = ast.unparse(param.annotation) if param.annotation else ""
                param_str = f"{param_name}: {type_hint}" if type_hint else param_name
                param_strings.append(param_str)
            def_line = f"def {node.name}({', '.join(param_strings)}):"
            func_info["interface"] = def_line

            # Process docstring to remove default parameters from Args
            docstring = ""
            if node.body and isinstance(node.body[0], ast.Expr):
                docstring_node = node.body[0]
                if isinstance(docstring_node.value, ast.Constant):
                    docstring = docstring_node.value.value

            cleaned_doc_lines = []
            in_args_section = False
            for line in docstring.split("\n"):
                stripped_line = line.strip()
                if stripped_line.lower().startswith("args:"):
                    in_args_section = True
                    cleaned_doc_lines.append(line)
                    continue
                if in_args_section:
                    if not stripped_line or stripped_line.startswith(
                        ("returns:", "raises:", "example:")
                    ):
                        in_args_section = False
                    elif ":" in stripped_line:
                        param_part = stripped_line.split(":", 1)[0].strip()
                        if param_part in default_params:
                            continue  # Skip lines for default parameters
                cleaned_doc_lines.append(line)

            func_info["description"] = "\n".join(cleaned_doc_lines).strip()

            # Build dict_args for required parameters
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
            func_info["dict_args"] = "\n".join(dict_args_lines)

            functions.append(func_info)

    return functions


if __name__ == "__main__":
    extract_plot_functions()
