# Generates solver-specific code (e.g., PuLP) and executes it.
import pulp
import google.generativeai as genai
from nlp_processor import GEMINI_API_KEY
import logging # Added for logging
import subprocess # For running code in a separate process
import sys # To get current python executable

# Configure Gemini API
genai.configure(api_key=GEMINI_API_KEY)

# Configure logging for this module specifically if needed, or rely on root logger
logger = logging.getLogger(__name__)
# Ensure logger is at least DEBUG level to see all messages. 
# The Flask app's main logging config will also influence this.
# For now, let's assume the root logger is configured appropriately.
# If not, uncomment and configure:
# logger.setLevel(logging.DEBUG)
# handler = logging.StreamHandler()
# formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# handler.setFormatter(formatter)
# logger.addHandler(handler)

def generate_pulp_code(model_plaintext: str) -> str:
    """
    Uses Gemini API to generate PuLP Python code from a mathematical model plaintext.
    
    Args:
        model_plaintext: The mathematical model in plaintext format
        
    Returns:
        str: Generated PuLP Python optimization code
    """
    logger.info("Attempting to generate PuLP code...")
    logger.debug(f"Input model_plaintext (first 200 chars):\\n{model_plaintext[:200]}...")
    # Create a prompt for Gemini to convert the model to PuLP code
    prompt = f"""
You are an expert Operations Research professional and Python programmer. 
Convert the following mathematical optimization model into executable PuLP Python code.

The mathematical model is:

{model_plaintext}

Follow these guidelines:
1. Import the necessary libraries (pulp). Allow numpy if essential for complex data structures, but prefer standard lists/dicts if possible.
2. Define all decision variables using `pulp.LpVariable` or `pulp.LpVariable.dicts`. Ensure variable names in the code match those in the model. Specify appropriate bounds (e.g., `lowBound=0`) and categories (e.g., `cat=pulp.LpContinuous`, `cat=pulp.LpInteger`, `cat=pulp.LpBinary`).
3. Create a PuLP model instance, e.g., `model = pulp.LpProblem("MyOptimizationProblem", pulp.LpMaximize)`. Determine `LpMaximize` or `LpMinimize` from the model's objective.
4. Define the objective function and add it to the model, e.g., `model += pulp.lpSum([...]), "Objective Function"`.
5. Add all constraints to the model one by one, e.g., `model += pulp.lpSum([...]) <= 100, "Constraint_Name_1"`.
6. Include the command to solve the model: `status = model.solve()`.
7. Add code to print the solution. This MUST include:
    a. The solution status: `print(f"Status: {{pulp.LpStatus[status]}}")`
    b. The optimal objective function value: `print(f"Objective Value: {{pulp.value(model.objective)}}")`
    c. The values of ALL decision variables.
        - For scalar variables (e.g., `my_var`):
          Use a check for `varValue` being `None`:
          ```python
          if my_var.varValue is not None:
              print(f"my_var = {{my_var.varValue}}")
          else:
              print(f"my_var = Not in solution or value is 0/None")
          ```
          Or, for assignment with a default if you need the value later:
          `my_var_val = my_var.varValue if my_var.varValue is not None else 0.0`

        - For indexed variables (e.g., `x[i,j]` where `i` is in `SET1` and `j` is in `SET2`):
          Iterate through ALL defined indices for that variable.
          ```python
          # Assuming x = pulp.LpVariable.dicts("x", (SET1, SET2), ...)
          # Assuming SET1 and SET2 are lists/ranges of indices used in the model definition
          for i in SET1:
              for j in SET2:
                  if x[(i,j)].varValue is not None: # Note: PuLP dicts use tuples for multi-indices
                      print(f"x[({{i}},{{j}})] = {{x[(i,j)].varValue}}")
                  else:
                      print(f"x[({{i}},{{j}})] = Not in solution or value is 0/None")
          ```
        - **IMPORTANT SYNTAX FOR CONDITIONAL (TERNARY) EXPRESSIONS:**
          If you use a ternary expression like `val = ... if ... else ...`, YOU MUST INCLUDE THE `else` part.
          CORRECT: `some_val = my_var.varValue if my_var.varValue is not None else 0.0`
          INCORRECT (SyntaxError): `some_val = my_var.varValue if my_var.varValue` (this is missing the `else` part!)
          INCORRECT (SyntaxError): `some_val = my_var.varValue if SomeOtherConditionWithoutElse`
          When in doubt, prefer full `if/else` blocks as shown in the examples above for clarity and safety.

8. Add meaningful comments to the Python code for readability.
9. Ensure the generated Python code is complete, correct, and can be executed directly.
10. The variable names, set names, and constraint names used in the PuLP code should correspond to those in the provided mathematical model.

Return ONLY the complete, executable Python code. Do not include any of your own explanations, apologies, or markdown formatting like "```python" or "```" in the output. Just the raw Python code.
"""
    logger.debug(f"Gemini Prompt (first 200 chars):\\n{prompt[:200]}...")

    # Call Gemini API to generate the code
    generation_config = {
        "temperature": 0.2,
        "top_p": 0.9,
        "top_k": 40,
        "max_output_tokens": 16384,
        "response_mime_type": "text/plain"
    }
    
    model = genai.GenerativeModel(
        model_name="gemini-2.5-flash-preview-04-17",
        generation_config=generation_config
    )
    
    generated_code = "" # Initialize to empty string
    try:
        logger.info("Sending request to Gemini API...")
        response = model.generate_content(prompt)
        logger.info("Received response from Gemini API.")
        logger.debug(f"Raw Gemini API response object: {response}") # Log the whole response object for inspection

        # Extract the PuLP code from the response
        if hasattr(response, 'text') and response.text:
            generated_code = response.text
            logger.debug(f"Extracted code from response.text (first 200 chars): {generated_code[:200]}...")
        elif hasattr(response, 'parts') and response.parts and hasattr(response.parts[0], 'text') and response.parts[0].text:
            generated_code = response.parts[0].text
            logger.debug(f"Extracted code from response.parts[0].text (first 200 chars): {generated_code[:200]}...")
        else:
            logger.warning("Gemini response does not contain 'text' or 'parts[0].text', or it is empty.")
            logger.debug(f"Response candidates: {response.candidates if hasattr(response, 'candidates') else 'N/A'}")
            logger.debug(f"Response prompt feedback: {response.prompt_feedback if hasattr(response, 'prompt_feedback') else 'N/A'}")
            return "" # Return empty if no usable code part found

        # Log the first few characters of potentially successful code
        logger.debug(f"Code snippet received (pre-cleaning, first 200 chars): {generated_code[:200]}...")

        # Clean the generated code: remove markdown fences
        cleaned_code = generated_code.strip()
        if cleaned_code.startswith("```python"):
            cleaned_code = cleaned_code[len("```python"):].lstrip() # Remove prefix and leading whitespace
            logger.debug("Removed '```python' prefix.")
        elif cleaned_code.startswith("```"):
            cleaned_code = cleaned_code[len("```"):].lstrip()
            logger.debug("Removed '```' prefix.")

        if cleaned_code.endswith("```"):
            cleaned_code = cleaned_code[:-len("```")].rstrip() # Remove suffix and trailing whitespace
            logger.debug("Removed '```' suffix.")
        
        logger.info(f"Successfully generated and cleaned PuLP code (length: {len(cleaned_code)}).")
        logger.debug(f"Cleaned code snippet (first 200 chars): {cleaned_code[:200]}...")
        return cleaned_code

    except Exception as e:
        logger.error(f"Exception during Gemini API call or code processing: {e}", exc_info=True)
        # It's useful to log the response even on error, if available
        if 'response' in locals() and response:
             logger.error(f"Gemini response object at time of error: {response}")
             logger.error(f"Response candidates at error: {response.candidates if hasattr(response, 'candidates') else 'N/A'}")
             logger.error(f"Response prompt feedback at error: {response.prompt_feedback if hasattr(response, 'prompt_feedback') else 'N/A'}")
        return "" # Return empty string on failure/blockage

# Placeholder for a sandboxed execution environment if needed.
# For now, we'll execute directly.

def generate_python_code(model_representation: dict, solver: str = "pulp") -> str:
    """
    Generates Python code for the specified solver from the internal model representation.
    """
    # TODO: Implement code generation logic for PuLP (and potentially OR-Tools).
    # This will involve translating the structured model (variables, objective, constraints)
    # into PuLP syntax.
    print(f"Generating Python code for {solver} (not yet implemented)...")
    if solver == "pulp":
        code = """
import pulp

# Create the model
model = pulp.LpProblem("MyORProblem", pulp.LpMinimize) # Or LpMaximize

# Define variables (example)
# x = pulp.LpVariable("x", lowBound=0, cat=pulp.LpContinuous)
# y = pulp.LpVariable.dicts("y", [1, 2, 3], lowBound=0, cat=pulp.LpInteger)

# Define objective function (example)
# model += x + pulp.lpSum(y[i] for i in [1,2,3]), "Objective Function"

# Define constraints (example)
# model += 2*x + y[1] <= 10, "Constraint1"

# Solve the problem
# status = model.solve()

# print(f"Status: {pulp.LpStatus[status]}")
# print(f"Objective value: {pulp.value(model.objective)}")
# for v in model.variables():
#     print(f"{v.name} = {v.varValue}")
"""
        return code
    else:
        return f"# Code generation for {solver} not implemented."

def run_solver_code(python_code: str) -> dict:
    """
    Executes the generated Python solver code in a separate process using subprocess.
    Captures stdout and stderr.

    Args:
        python_code (str): The Python code string to execute.

    Returns:
        dict: A dictionary containing:
              'error' (bool): True if an error occurred, False otherwise.
              'output' (str): The stdout from the executed code.
              'error_details' (str): The stderr from the executed code or an error message.
              'raw_output' (str): Concatenation of stdout and stderr for debugging.
    """
    logging.info("Attempting to run solver code via subprocess...")
    try:
        # Use the same Python interpreter that's running the Flask app
        python_executable = sys.executable
        
        process = subprocess.Popen(
            [python_executable, "-c", python_code],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True, # Decode stdout/stderr as text
            universal_newlines=True # Ensure cross-platform newline handling (might be redundant with text=True)
        )
        
        # Communicate with the process, get output and errors
        # Set a timeout to prevent hanging indefinitely (e.g., 30 seconds)
        stdout, stderr = process.communicate(timeout=30) 
        
        return_code = process.returncode
        raw_output = f"--- STDOUT ---\n{stdout}\n--- STDERR ---\n{stderr}"
        logging.info(f"Subprocess finished with return code: {return_code}")
        logging.debug(f"Raw output from subprocess:\n{raw_output}")

        if return_code != 0:
            # Error occurred during execution
            error_message = f"Code execution failed with return code {return_code}."
            if stderr:
                error_message += f"\nDetails:\n{stderr.strip()}"
            elif stdout: # Sometimes errors are printed to stdout
                error_message += f"\nOutput (may contain error info):\n{stdout.strip()}"
            
            return {
                "error": True,
                "output": stdout.strip(), 
                "error_details": stderr.strip() if stderr else "Execution failed with non-zero exit code. Check raw output.",
                "raw_output": raw_output
            }
        else:
            # Successful execution
            return {
                "error": False, 
                "output": stdout.strip(), 
                "error_details": stderr.strip(), # Stderr might contain warnings even on success
                "raw_output": raw_output
            }
            
    except subprocess.TimeoutExpired:
        logging.error("Code execution timed out.")
        return {
            "error": True, 
            "output": "", 
            "error_details": "Code execution timed out after 30 seconds.",
            "raw_output": "Timeout occurred."
        }
    except Exception as e:
        logging.error(f"Exception during subprocess execution: {e}", exc_info=True)
        return {
            "error": True, 
            "output": "", 
            "error_details": f"An unexpected error occurred while trying to run the code: {str(e)}",
            "raw_output": f"Exception: {str(e)}"
        }