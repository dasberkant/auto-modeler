# Converts NLP output (structured components) into a formal mathematical model.

# Placeholder for how the structured OR model will be represented internally.
# This could be a custom class or a dictionary structure.

import re # For escaping special LaTeX characters

def formulate_model_from_nlp(parsed_components: dict) -> dict:
    """
    Takes the structured components from NLP and formulates an internal
    representation of the mathematical model.
    Currently, this function is a pass-through, assuming parsed_components
    is already in a suitable format for rendering.
    Future: Could transform parsed_components into a more formal class-based model.
    """
    print(f"Formulating model from NLP output (pass-through for now)...")
    return parsed_components

def latex_escape(text, is_math_mode=False):
    """Escapes special LaTeX characters in a string. Handles math mode differently."""
    if not isinstance(text, str):
        text = str(text)
    
    if is_math_mode:
        # In math mode, underscores and carets are fine, but other things might need care.
        # This is a simplification; robust math escaping can be complex.
        text = text.replace('\\ ',' ') # normalize backslash space
        # Characters like $, %, #, &, { } might need escaping if they are not part of commands.
        # However, we assume expressions from Gemini are somewhat LaTeX-aware.
        pass # Minimal escaping for now in math mode
    else:
        # For regular text
        replacements = {
            "&": r"\\&",
            "%": r"\\%",
            "$": r"\\$",
            "#": r"\\#",
            "_": r"\\_",
            "{": r"\\{",
            "}": r"\\}",
            "~": r"\\textasciitilde{}",
            "^": r"\\textasciicircum{}",
            "\\": r"\\textbackslash{}",
        }
        # Create a regex to find all special characters and replace them
        # The order in `replacements` might matter if one replacement creates another special char.
        # A safer way is to iterate and replace, or build a more complex regex.
        # For simplicity here, let's iterate (less efficient but safer for overlap):
        for char, replacement in replacements.items():
            text = text.replace(char, replacement)
    return text

def render_model_latex(model_representation: dict) -> str:
    """Renders the internal model representation as a full LaTeX document string for PDF compilation."""
    if not isinstance(model_representation, dict):
        # Return a valid LaTeX document indicating an error
        return ("\\documentclass{article}\\usepackage{amsmath}\\begin{document}" 
                "Error: Model representation is not a valid dictionary." 
                "\\end{document}")
    
    # Check if there was an error in the model representation
    if 'error' in model_representation:
        error_msg = latex_escape(model_representation.get('error', 'Unknown error'))
        return (
            "\\documentclass{article}\n"
            "\\usepackage{amsmath}\n"
            "\\usepackage{xcolor}\n"
            "\\begin{document}\n"
            "\\section*{Error in Model Generation}\n"
            f"\\textcolor{{red}}{{Error: {error_msg}}}\n\n"
            "Please check your problem statement and try again.\n"
            "\\end{document}"
        )

    # Create more stable LaTeX with safer defaults
    latex_doc = [
        "\\documentclass{article}",
        "\\usepackage[utf8]{inputenc}",
        "\\usepackage[T1]{fontenc}",
        "\\usepackage{amsmath} % For mathematical typesetting",
        "\\usepackage{amsfonts} % For math fonts like R, Z",
        "\\usepackage{amssymb} % For various symbols",
        "\\usepackage{array} % For better table formatting",
        "\\usepackage{booktabs} % For professional tables",
        "\\usepackage[margin=1in]{geometry} % Sensible margins",
        "\\usepackage{parskip} % Use space between paragraphs instead of indent",
        "\\usepackage{xcolor} % For colored text",
        "% Define safer math environments",
        "\\newcommand{\\safemath}[1]{\\ensuremath{#1}}",
        "\\title{Operations Research Model Formulation}",
        "\\author{Auto-Modeler}",
        "\\date{\\today}",
        "\\begin{document}",
        "\\maketitle",
        "\\section*{Problem Overview}",
        "This document presents the mathematical formulation of the Operations Research problem using standard notation.",
    ]
    
    # Helper function to safely handle math content
    def safe_math(content):
        if not content:
            return ""
            
        # If already wrapped in math delimiters, extract content
        if isinstance(content, str):
            if content.startswith('$') and content.endswith('$'):
                content = content[1:-1]  # Remove delimiters
        
        # Escape troublesome characters
        if isinstance(content, str):
            # Protect % characters
            content = content.replace('%', '\\%')
            # Ensure _ has a preceding backslash in non-math contexts
            if '_' in content and '\\' not in content:
                content = content.replace('_', '\\_')
                
        return f"\\safemath{{{content}}}"
    
    # --- Sets ---
    if 'sets' in model_representation and model_representation['sets']:
        latex_doc.append("\\section*{Sets}")
        latex_doc.append("\\begin{itemize}")
        for s in model_representation['sets']:
            # Extract both parts if in "Name ($X$)" format
            parts = s.split('(')
            if len(parts) > 1 and ')' in parts[1]:
                name = parts[0].strip()
                symbol = '('.join(parts[1:]).strip()
                latex_doc.append(f"    \\item {name} ({symbol}")
            else:
                latex_doc.append(f"    \\item {s}")
        latex_doc.append("\\end{itemize}")

    # --- Parameters ---
    if 'parameters' in model_representation and model_representation['parameters']:
        latex_doc.append("\\section*{Parameters}")
        latex_doc.append("\\begin{itemize}")
        for k, v in model_representation['parameters'].items():
            # Remove math delimiters if present (we'll handle them safely)
            param_key = k
            if param_key.startswith('$') and param_key.endswith('$'):
                param_key = param_key[1:-1]
                
            # Make the parameter a safe command
            latex_doc.append(f"    \\item \\safemath{{{param_key}}}: {v}")
        latex_doc.append("\\end{itemize}")

    # --- Decision Variables ---
    if 'variables' in model_representation and model_representation['variables']:
        latex_doc.append("\\section*{Decision Variables}")
        latex_doc.append("\\begin{itemize}")
        for k, v in model_representation['variables'].items():
            # Remove math delimiters if present (we'll handle them safely)
            var_key = k
            if var_key.startswith('$') and var_key.endswith('$'):
                var_key = var_key[1:-1]
                
            # Make the variable a safe command
            latex_doc.append(f"    \\item \\safemath{{{var_key}}}: {v}")
        latex_doc.append("\\end{itemize}")

    # --- Objective Function ---
    if 'objective' in model_representation and model_representation['objective']:
        obj = model_representation['objective']
        obj_type = obj.get('type', 'Objective').capitalize()
        obj_expr = obj.get('expression', 'N/A') 
        latex_doc.append(f"\\section*{{{obj_type} Function}}")
        
        # Remove math delimiters if present
        if isinstance(obj_expr, str) and obj_expr.startswith('$') and obj_expr.endswith('$'):
            obj_expr = obj_expr[1:-1]
        
        # Put the objective in a display equation for better rendering
        latex_doc.append("\\begin{center}")
        latex_doc.append(f"{obj_type}:")
        latex_doc.append("\\begin{equation*}")
        latex_doc.append(f"{obj_expr}")
        latex_doc.append("\\end{equation*}")
        latex_doc.append("\\end{center}")

    # --- Constraints ---
    if 'constraints' in model_representation and model_representation['constraints']:
        latex_doc.append("\\section*{Constraints}")
        latex_doc.append("\\noindent\\textbf{Subject to:}")
        latex_doc.append("\\begin{itemize}")
        
        for constr in model_representation['constraints']:
            # Split into formula and description if possible
            parts = constr.split('(', 1)
            formula = parts[0].strip()
            description = f"({parts[1]}" if len(parts) > 1 else ""
            
            # Extract math content if it's wrapped in delimiters
            if formula.startswith('$') and formula.endswith('$'):
                formula = formula[1:-1]
            
            # Use a centered equation for each constraint
            latex_doc.append("    \\item")
            latex_doc.append("    \\begin{center}")
            latex_doc.append("    \\begin{minipage}{0.9\\textwidth}")
            latex_doc.append("    \\begin{equation*}")
            latex_doc.append(f"    {formula}")
            latex_doc.append("    \\end{equation*}")
            if description:
                latex_doc.append(f"    \\centering{{{description}}}")
            latex_doc.append("    \\end{minipage}")
            latex_doc.append("    \\end{center}")
            
        latex_doc.append("\\end{itemize}")

    # --- Data (Optional) ---
    if 'data' in model_representation and model_representation['data']:
        latex_doc.append("\\section*{Data Values}")
        latex_doc.append("\\begin{itemize}")
        for k, v_data in model_representation['data'].items():
            # Clean up key (remove math delimiters if present)
            data_key = k
            if data_key.startswith('$') and data_key.endswith('$'):
                data_key = data_key[1:-1]
                
            if isinstance(v_data, dict):
                # Create a small table for dictionary data
                latex_doc.append(f"    \\item \\safemath{{{data_key}}}:")
                latex_doc.append("    \\begin{center}")
                latex_doc.append("    \\begin{tabular}{lr}")
                latex_doc.append("    \\toprule")
                latex_doc.append("    \\textbf{Index} & \\textbf{Value} \\\\")
                latex_doc.append("    \\midrule")
                for d_key, d_val in v_data.items():
                    # Escape any special characters
                    safe_key = str(d_key).replace("_", "\\_").replace("%", "\\%")
                    latex_doc.append(f"    {safe_key} & {d_val} \\\\")
                latex_doc.append("    \\bottomrule")
                latex_doc.append("    \\end{tabular}")
                latex_doc.append("    \\end{center}")
            elif isinstance(v_data, list):
                # Format list items safely
                safe_items = []
                for item in v_data:
                    safe_items.append(str(item).replace("_", "\\_").replace("%", "\\%"))
                data_str = ", ".join(safe_items)
                latex_doc.append(f"    \\item \\safemath{{{data_key}}}: $[{data_str}]$")
            else:
                # Format single value safely
                safe_val = str(v_data).replace("_", "\\_").replace("%", "\\%")
                latex_doc.append(f"    \\item \\safemath{{{data_key}}}: {safe_val}")
        latex_doc.append("\\end{itemize}")

    if len(latex_doc) <= 10: # Just preamble
        latex_doc.append("No model components found to render or model structure is not as expected.")
    
    latex_doc.append("\\end{document}")
    return "\n".join(latex_doc)

def render_model_plaintext(model_representation: dict) -> str:
    """Renders the internal model representation as plaintext in a structured OR style."""
    if not isinstance(model_representation, dict):
        return "Error: Model representation is not a valid dictionary."

    plain_parts = []
    order = ['Sets', 'Parameters', 'Variables', 'Objective Function', 'Constraints', 'Data']
    key_map = { # Map display name to potential keys in the dictionary
        'Sets': 'sets',
        'Parameters': 'parameters',
        'Variables': 'variables',
        'Objective Function': 'objective',
        'Constraints': 'constraints',
        'Data': 'data'
    }

    for display_name in order:
        actual_key = key_map.get(display_name)
        if actual_key and actual_key in model_representation and model_representation[actual_key]:
            content = model_representation[actual_key]
            plain_parts.append(f"\n--- {display_name.upper()} ---")
            
            if display_name == "Objective Function" and isinstance(content, dict):
                obj_type = content.get('type', 'Objective').capitalize()
                obj_expr = content.get('expression', 'N/A')
                plain_parts.append(f"{obj_type}: {obj_expr}")
            elif isinstance(content, list):
                for item_in_list in content:
                    plain_parts.append(f"- {str(item_in_list)}")
            elif isinstance(content, dict):
                for k, v in content.items():
                    plain_parts.append(f"  {k}: {str(v)}")
            else:
                plain_parts.append(str(content))
            plain_parts.append("") # Add a newline for spacing
            
    if not plain_parts:
        return "No model components found to render."
    return "\n".join(plain_parts) 