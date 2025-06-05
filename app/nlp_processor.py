# Handles interaction with Gemini API for NLP tasks

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get Gemini API Key from environment variables
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Initialize Gemini client (google.generativeai)
genai_model = None
if GEMINI_API_KEY:
    try:
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_API_KEY)
        # You can specify the model here, e.g., 'gemini-1.5-flash', 'gemini-pro', etc.
        genai_model = genai.GenerativeModel('gemini-2.5-flash-preview-04-17') 
        print("Gemini client initialized successfully.")
    except ImportError:
        print("ERROR: The 'google-generativeai' library is not installed. Please install it by running: pip install google-generativeai")
    except Exception as e:
        print(f"ERROR: Failed to initialize Gemini client: {e}")
else:
    print("WARNING: GEMINI_API_KEY environment variable is not set. Please set it in your .env file. AI functionalities will be limited.")

def optimize_problem_statement(raw_problem_statement: str) -> str:
    """Calls Gemini API to refine and optimize the raw problem statement for OR modeling."""
    if not genai_model:
        print("ERROR: Gemini model not initialized. Cannot optimize problem statement.")
        return raw_problem_statement # Return original if model not available

    prompt = f"""You are an expert Operations Research modeler. Your task is to refine and clarify the following problem statement to make it highly suitable for automatic mathematical model formulation. 
    Do not solve the problem or create the mathematical model yourself. 
    Your goal is to rephrase and structure the given problem statement clearly, ensuring all essential information is explicit.
    Ensure that:
    - The language is precise.
    - Ambiguities are minimized.
    - Objectives, constraints, known values, and decision factors are clearly stated or easily inferable.
    - If critical information seems missing for a typical OR problem of the described type, you can note it, but prioritize rephrasing what IS provided.
    Output ONLY the refined problem statement text, without any of your own conversational text or preambles.

    Original Problem Statement:
    ---BEGIN ORIGINAL STATEMENT---
    {raw_problem_statement}
    ---END ORIGINAL STATEMENT---

    Refined Problem Statement for OR Modeling:
    """

    try:
        response = genai_model.generate_content(prompt)
        optimized_statement = response.text.strip()
        # Basic cleaning, sometimes LLMs add extra quotes or markers
        if optimized_statement.startswith("Refined Problem Statement for OR Modeling:"):
            optimized_statement = optimized_statement.replace("Refined Problem Statement for OR Modeling:", "").strip()
        if optimized_statement.startswith('"'') and optimized_statement.endswith('"'') and optimized_statement.count('"'') == 2:
            optimized_statement = optimized_statement[1:-1]
        print(f"Optimized problem statement: {optimized_statement}") # For debugging
        return optimized_statement
    except Exception as e:
        print(f"ERROR: Failed to optimize problem statement with Gemini: {e}")
        return raw_problem_statement # Fallback to original statement

def parse_problem_statement(problem_statement: str) -> dict:
    """Calls Gemini API to parse the problem statement into structured components."""
    if not genai_model:
        print("ERROR: Gemini model not initialized. Cannot parse problem statement.")
        # Return a mock/error structure or raise an exception
        return {"error": "Gemini model not initialized"}
    
    prompt = f"""As an Operations Research expert, you are tasked with converting a problem statement into a structured OR model ready for LaTeX rendering. Follow these strict guidelines:

1. Analyze the problem statement thoroughly to extract all OR components.
2. Format your output as a valid JSON object containing these components:

# LaTeX FORMATTING REQUIREMENTS
- All mathematical expressions MUST include proper LaTeX math delimiters ($...$)
- Use proper LaTeX commands for all mathematical operations:
  - Summations: $\\sum_{{i \\in I}}$
  - Products: $\\prod_{{i \\in I}}$
  - For all: $\\forall i \\in I$
  - There exists: $\\exists i \\in I$
  - Less than or equal: $\\leq$
  - Greater than or equal: $\\geq$
  - Element of: $\\in$
  - Proper subscripts: $x_{{ij}}$ (with double braces for multi-character subscripts)
  - Fractions: $\\frac{{numerator}}{{denominator}}$
- All mathematical expressions must strictly conform to LaTeX syntax
- Escape all special LaTeX characters ($, %, &, #, etc.) with a backslash

**Sets**:
- Define all sets using proper mathematical notation
- Format set names using LaTeX syntax: e.g., "Products ($P$)" instead of "Products (P)"
- Ensure all set symbols are enclosed in math delimiters: $P$, $I$, etc.

**Parameters**:
- Use proper LaTeX notation for all mathematical symbols
- Format parameter descriptions with units: e.g., "Cost of product $p$ ($/unit)"
- Use subscripts with underscores in math mode: $Cost_{{i,j}}$ not Cost_i,j

**Variables**:
- Define all decision variables using proper LaTeX syntax
- Specify each variable's domain (Continuous, Integer, Binary)
- Include upper/lower bounds in mathematical notation: $x_i \\geq 0$

**Objective Function**:
- Specify whether Minimize or Maximize
- Express the objective function using proper LaTeX syntax for summations, products, etc.
- Example: "Minimize $\\sum_{{i \\in I}} \\sum_{{j \\in J}} c_{{ij}} x_{{ij}}$"

**Constraints**:
- Format each constraint using proper LaTeX syntax
- Include descriptive names for constraints
- Example: "$\\sum_{{j \\in J}} x_{{ij}} \\leq b_i$ for all $i \\in I$ (Supply constraints)"

**Data** (if provided):
- Format structured data appropriately in JSON format
- For matrices, use proper multi-dimensional structure

Problem Statement:
---BEGIN PROBLEM STATEMENT---
{problem_statement}
---END PROBLEM STATEMENT---

Respond ONLY with a valid, parseable JSON object with LaTeX-ready formatted content. Ensure all mathematical notation is properly formatted for direct rendering in LaTeX documents.

# IMPORTANT: JSON FORMAT GUIDELINES
- Ensure all keys and values are properly quoted as required by JSON
- All backslashes must be double escaped (\\\\\\\\) in the JSON for LaTeX commands
- For dollar signs in actual costs, write them as '\$' with a single backslash
- Do not include unescaped line breaks in strings
- All mathematical expressions must be enclosed in $...$ for inline math
- Test your JSON for validity before returning it

Example of desired JSON structure (adapt for the specific problem):
{{ 
    "sets": [
        "Warehouses ($W$)",
        "Retailers ($R$)"
    ],
    "parameters": {{ 
        "$s_w$": "Supply at warehouse $w$ (units)",
        "$d_r$": "Demand at retailer $r$ (units)", 
        "$c_{{wr}}$": "Cost to ship 1 unit from warehouse $w$ to retailer $r$ (\\$)"
    }},
    "variables": {{ 
        "$x_{{wr}}$": "Quantity shipped from warehouse $w$ to retailer $r$ (units, $x_{{wr}} \\geq 0$, Continuous)"
    }},
    "objective": {{ 
        "type": "Minimize", 
        "expression": "$\\sum_{{w \\in W}} \\sum_{{r \\in R}} c_{{wr}} x_{{wr}}$"
    }},
    "constraints": [
        "$\\sum_{{r \\in R}} x_{{wr}} \\leq s_w$ for all $w \\in W$ (Supply constraints)",
        "$\\sum_{{w \\in W}} x_{{wr}} \\geq d_r$ for all $r \\in R$ (Demand constraints)"
    ],
    "data": {{ 
        "$W$": ["W1", "W2"],
        "$R$": ["R1", "R2", "R3"],
        "$s$": {{"W1": 100, "W2": 150}},
        "$d$": {{"R1": 70, "R2": 80, "R3": 90}},
        "$c$": {{ 
            "W1,R1": 10, 
            "W1,R2": 12, 
            "W1,R3": 14,
            "W2,R1": 11, 
            "W2,R2": 9, 
            "W2,R3": 13
        }}
    }}
}}
"""
    
    try:
        response = genai_model.generate_content(prompt)
        
        # Attempt to parse the response text as JSON
        # Gemini might return the JSON within triple backticks or with other surrounding text
        response_text = response.text.strip()
        if response_text.startswith("```json"):
            response_text = response_text[7:] # Remove ```json
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        
        # Clean up any problematic escape sequences before parsing JSON
        response_text = response_text.strip()
        
        # Fix common escape sequence issues in the JSON
        # 1. Fix escaped dollar signs in descriptions
        response_text = response_text.replace('(\\$/unit)', r'($/unit)')
        response_text = response_text.replace('(\\$)', r'($)')
        
        # 2. Fix JSON strings with backslashes that aren't properly escaped
        import re
        
        # Fix LaTeX command escaping in a targeted way
        def fix_latex_escapes(match):
            # Get the content between quotes
            content = match.group(1)
            # Replace single backslashes with double backslashes except when already doubled
            fixed = re.sub(r'(?<!\\)\\(?!\\)', r'\\\\', content)
            return f'"{fixed}"'
        
        # Apply fixes to string values in the JSON
        response_text = re.sub(r'"((?:\\.|[^"\\])*)"', fix_latex_escapes, response_text)
        
        import json
        parsed_output = json.loads(response_text.strip())
        return parsed_output
    except Exception as e:
        print(f"ERROR: Failed to parse problem statement with Gemini or parse its JSON output: {e}")
        print(f"Gemini raw response was: {response.text if 'response' in locals() else 'No response object'}")
        
        # If JSON parsing failed, attempt to fix the most common issues with escape sequences
        if 'response_text' in locals():
            try:
                # Handle the specific escape sequence issue
                cleaned_text = response_text.replace('\\$', '$')
                parsed_output = json.loads(cleaned_text)
                return parsed_output
            except Exception as e2:
                print(f"Failed second attempt to parse JSON after escaping fixes: {e2}")
                
                # Last resort - create a simplified model based on the raw text
                try:
                    # Extract model parts from raw text to build a simplified model
                    simplified_model = {
                        "error": f"JSON parsing error, but partial extraction was attempted: {e}",
                        "raw_output": response.text if 'response' in locals() else 'N/A'
                    }
                    
                    # Try to identify basic components from the raw text
                    if '"sets"' in response_text:
                        simplified_model["sets"] = ["Extracted sets failed - see raw output"]
                    
                    if '"parameters"' in response_text:
                        simplified_model["parameters"] = {"Error": "Parameters extraction failed"}
                    
                    if '"variables"' in response_text:
                        simplified_model["variables"] = {"Error": "Variables extraction failed"}
                    
                    if '"objective"' in response_text:
                        simplified_model["objective"] = {
                            "type": "Extracted objective failed",
                            "expression": "See raw output"
                        }
                    
                    if '"constraints"' in response_text:
                        simplified_model["constraints"] = ["Constraints extraction failed"]
                        
                    return simplified_model
                except:
                    # Final fallback
                    return {"error": f"Failed to process with Gemini: {e}. Raw output: {response.text if 'response' in locals() else 'N/A'}"}
        
        # Fallback or re-throw
        return {"error": f"Failed to process with Gemini: {e}. Raw output: {response.text if 'response' in locals() else 'N/A'}"}

def suggest_code_revision(error_traceback: str, current_code: str) -> str:
    """Calls Gemini API to suggest revisions for erroneous solver code."""
    # TODO: Implement API call to Gemini
    print(f"Suggesting code revision for error (not yet implemented): {error_traceback[:50]}...")
    return "# Revised code to be filled by Gemini API"

def diagnose_infeasibility(model_details: dict) -> str:
    """Calls Gemini API to diagnose infeasibility/unboundedness issues."""
    # TODO: Implement API call to Gemini
    print(f"Diagnosing infeasibility (not yet implemented)...")
    return "Suggested model revisions for infeasibility to be filled by Gemini API"

def comment_on_reasonableness(solution_details: dict) -> str:
    """Calls Gemini API to comment on model reasonableness and suggest sensitivity analysis."""
    # TODO: Implement API call to Gemini
    print(f"Commenting on reasonableness (not yet implemented)...")
    return "Comments on reasonableness and sensitivity analysis to be filled by Gemini API" 