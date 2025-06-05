from flask import Flask, render_template, request, jsonify, session
import sys
import os
import logging # For better logging
import subprocess # Added for running code
import traceback # Added for error handling

# Adjust path to import modules from the 'app' directory
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from nlp_processor import parse_problem_statement, GEMINI_API_KEY, optimize_problem_statement
from model_formulator import formulate_model_from_nlp, render_model_plaintext
# solver_engine and validator imports will be used later
from solver_engine import generate_pulp_code
# from validator import perform_sanity_checks, check_model_reasonableness
from validator import validate_execution_results

app = Flask(__name__, template_folder='templates', static_folder='static')

# Configure secret key for sessions
app.secret_key = os.environ.get('SECRET_KEY', 'auto-modeler-dev-key-change-in-production')

# Setup logging
logging.basicConfig(level=logging.DEBUG)

# Configure Gemini (ensure the API key is set in nlp_processor.py)
# This setup is from nlp_processor.py, ensuring it's initialized when the app starts.
if GEMINI_API_KEY == "YOUR_GEMINI_API_KEY_HERE" or not GEMINI_API_KEY:
    app.logger.warning("Gemini API Key is not set or is placeholder in app/nlp_processor.py. AI features may not work.")
else:
    try:
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_API_KEY)
        # model = genai.GenerativeModel('gemini-pro') # or your chosen model from nlp_processor.py
        app.logger.info("Gemini API configured via nlp_processor settings.")
    except ImportError:
        app.logger.error("google-generativeai library not found. Please install it: pip install google-generativeai")
    except Exception as e:
        app.logger.error(f"Could not configure Gemini API: {e}")

@app.route('/')
def index():
    # Check if user has provided API key
    api_key_provided = 'gemini_api_key' in session and session['gemini_api_key']
    return render_template('index.html', api_key_provided=api_key_provided)

@app.route('/set_api_key', methods=['POST'])
def set_api_key():
    """Set the user's Gemini API key in the session."""
    try:
        api_key = request.form.get('api_key', '').strip()
        
        if not api_key:
            return jsonify({"error": "API key cannot be empty."}), 400
            
        if not api_key.startswith('AIzaSy'):
            return jsonify({"error": "Invalid API key format. Gemini API keys start with 'AIzaSy'."}), 400
        
        # Test the API key by making a simple request
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-2.0-flash-exp')
            
            # Simple test to validate the key
            response = model.generate_content("Hello")
            
            # If we get here, the API key works
            session['gemini_api_key'] = api_key
            app.logger.info("API key successfully validated and stored in session.")
            
            return jsonify({"success": True, "message": "API key validated and saved successfully!"})
            
        except Exception as e:
            app.logger.error(f"API key validation failed: {e}")
            return jsonify({"error": f"Invalid API key or API error: {str(e)}"}), 400
            
    except Exception as e:
        app.logger.error(f"Error in /set_api_key: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route('/clear_api_key', methods=['POST'])
def clear_api_key():
    """Clear the user's API key from the session."""
    try:
        session.pop('gemini_api_key', None)
        return jsonify({"success": True, "message": "API key cleared successfully!"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/optimize_statement', methods=['POST'])
def optimize_statement_route():
    try:
        # Check if user has provided API key
        api_key = session.get('gemini_api_key')
        if not api_key:
            return jsonify({"error": "Please provide your Gemini API key first."}), 400
            
        problem_statement_raw = request.form['problem_statement_raw']
        if not problem_statement_raw.strip():
            return jsonify({"error": "Problem statement cannot be empty."}), 400
            
        app.logger.info(f"Optimizing raw statement: {problem_statement_raw[:100]}...")
        optimized_statement = optimize_problem_statement(problem_statement_raw, api_key)
        app.logger.info(f"Optimized statement: {optimized_statement[:100]}...")
        
        return jsonify({"optimized_statement": optimized_statement})
    except Exception as e:
        app.logger.error(f"Error in /optimize_statement: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route('/formulate_model', methods=['POST'])
def formulate_model_route():
    try:
        # Check if user has provided API key
        api_key = session.get('gemini_api_key')
        if not api_key:
            return jsonify({"error": "Please provide your Gemini API key first."}), 400
            
        optimized_statement = request.form['optimized_statement']
        if not optimized_statement.strip():
            return jsonify({"error": "Optimized problem statement is missing."}), 400

        app.logger.info(f"Formulating model from: {optimized_statement[:100]}...")

        # STEP 1: Parse problem statement (NLP) using the optimized version
        parsed_components = parse_problem_statement(optimized_statement, api_key)
        
        if 'error' in parsed_components or not isinstance(parsed_components, dict):
            error_detail = parsed_components.get('error', 'Unknown parsing error or invalid format.') if isinstance(parsed_components, dict) else "Invalid format received from parser."
            app.logger.error(f"Error parsing statement: {error_detail}")
            # Return an error to the user
            raw_output_info = parsed_components.get('raw_output', 'N/A') if isinstance(parsed_components, dict) else str(parsed_components)
            return jsonify({
                "error": f"Failed to parse the problem statement: {error_detail}. Raw parser output: {raw_output_info}"
            }), 500
        
        app.logger.info(f"Successfully parsed components: {list(parsed_components.keys())}")

        # STEP 2: Formulate mathematical model 
        model_representation = formulate_model_from_nlp(parsed_components)
        
        # STEP 3: Generate plaintext representation only
        model_plaintext = render_model_plaintext(model_representation)
        app.logger.info("Model rendered to plaintext.")

        return jsonify({
            "model_plaintext": model_plaintext
        })

    except Exception as e:
        app.logger.error(f"Error in /formulate_model: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route('/generate_code', methods=['POST'])
def generate_code_route():
    try:
        # Check if user has provided API key
        api_key = session.get('gemini_api_key')
        if not api_key:
            return jsonify({"error": "Please provide your Gemini API key first."}), 400
            
        model_plaintext = request.form['model_plaintext']
        if not model_plaintext.strip():
            return jsonify({"error": "Mathematical model is missing."}), 400

        app.logger.info("Generating PuLP Python code...")
        
        # Generate the PuLP code using Gemini
        python_code = generate_pulp_code(model_plaintext, api_key)
        
        if not python_code or not python_code.strip():
            app.logger.error("Code generation by AI failed: Received empty or whitespace-only code from solver_engine.")
            return jsonify({
                "error": "AI code generation failed to produce code. The model might have encountered an internal issue, or the request could have been filtered. Please check server logs for more detailed information from the AI service."
            }), 500
        
        app.logger.info("Successfully generated PuLP Python code.")
        
        return jsonify({
            "python_code": python_code
        })
        
    except Exception as e:
        app.logger.error(f"Error in /generate_code: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route('/run_code', methods=['POST'])
def run_code_route():
    # IMPORTANT SECURITY WARNING:
    # Executing arbitrary Python code received from a client is highly insecure
    # and can expose your server to significant vulnerabilities.
    # The following is a basic example and SHOULD NOT be used in a production
    # environment without extreme caution and proper sandboxing or other
    # security measures. Consider using a dedicated, isolated execution
    # environment or service.

    try:
        python_code = request.form['python_code']
        if not python_code.strip():
            return jsonify({"error": "No Python code provided.", "error_details": "Code string is empty."}), 400

        app.logger.info(f"Attempting to run code (first 100 chars): {python_code[:100]}...")

        # Placeholder for actual secure code execution.
        # For a real application, you MUST use a secure, sandboxed environment.
        # Example using subprocess (still needs careful handling):
        try:
            # Using sys.executable to ensure we're using the same Python interpreter
            # as the Flask app. Timeout is important to prevent long-running scripts.
            process = subprocess.run(
                [sys.executable, '-c', python_code],
                capture_output=True,
                text=True,
                timeout=30, # Set a timeout (e.g., 30 seconds)
                check=False # Do not raise CalledProcessError for non-zero exit codes
            )
            
            if process.returncode == 0:
                app.logger.info("Code executed successfully.")
                return jsonify({
                    "output": process.stdout,
                    "error": None, # Explicitly state no error
                    "error_details": None,
                    "raw_output": process.stdout # For consistency if needed
                })
            else:
                app.logger.error(f"Code execution failed with return code {process.returncode}")
                app.logger.error(f"Stderr: {process.stderr}")
                return jsonify({
                    "error": "Code execution failed.", 
                    "error_details": process.stderr or "Unknown execution error (non-zero return code).",
                    "raw_output": process.stdout + "\n" + process.stderr # Combine stdout and stderr for context
                }), 200 # Return 200 because the API call itself was successful, but code execution failed
                       # The client-side JS checks for the 'error' key in the JSON.

        except subprocess.TimeoutExpired:
            app.logger.error("Code execution timed out.")
            return jsonify({
                "error": "Execution timed out.",
                "error_details": "The submitted code took too long to execute.",
                "raw_output": "Timeout occurred after 30 seconds."
            }), 200 # As above, API call itself is fine.
        except Exception as exec_e:
            app.logger.error(f"Exception during subprocess execution: {exec_e}", exc_info=True)
            return jsonify({
                "error": "Failed to execute code due to an internal error.",
                "error_details": str(exec_e),
                "raw_output": traceback.format_exc()
            }), 500 # This is a server-side issue with the execution attempt itself.

    except KeyError:
        app.logger.error("KeyError: 'python_code' not found in request form.")
        return jsonify({"error": "Missing 'python_code' in request.", "error_details": "The 'python_code' field was not found in the form data."}), 400
    except Exception as e:
        app.logger.error(f"Error in /run_code: {e}", exc_info=True)
        return jsonify({"error": "An unexpected error occurred on the server.", "error_details": str(e)}), 500

@app.route('/validate_results', methods=['POST'])
def validate_results_route():
    """
    Endpoint to validate model execution results using Gemini AI.
    Expects problem_statement, model_plaintext, python_code, and execution_output in the request.
    Returns a validation analysis with assessment, suggestions, and confidence level.
    """
    try:
        # Get all required inputs
        problem_statement = request.form.get('problem_statement', '')
        model_plaintext = request.form.get('model_plaintext', '')
        python_code = request.form.get('python_code', '')
        execution_output = request.form.get('execution_output', '')
        
        # Basic validation
        if not execution_output.strip():
            return jsonify({
                "error": "No execution output provided.",
                "error_details": "Model execution output is required for validation."
            }), 400
            
        app.logger.info("Validating optimization model results...")
        
        # Call the validation function
        validation_results = validate_execution_results(
            problem_statement=problem_statement,
            model_plaintext=model_plaintext,
            python_code=python_code,
            execution_output=execution_output
        )
        
        app.logger.info(f"Validation complete. Validity status: {validation_results.get('validity_status', 'Unknown')}")
        
        return jsonify(validation_results)
        
    except Exception as e:
        app.logger.error(f"Error in /validate_results: {e}", exc_info=True)
        return jsonify({
            "error": "An error occurred during validation.",
            "error_details": str(e)
        }), 500

if __name__ == '__main__':
    # Make sure to create the 'static' and 'templates' directories in 'app/ui/'
    # This check might be redundant if you ensure they exist, but good for robustness.
    ui_dir = os.path.dirname(__file__)
    if not os.path.exists(os.path.join(ui_dir, 'static')):
        os.makedirs(os.path.join(ui_dir, 'static'))
    if not os.path.exists(os.path.join(ui_dir, 'templates')):
        os.makedirs(os.path.join(ui_dir, 'templates'))
    
    # Get port from environment variable (for deployment) or use 5000 for local
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
    
    app.run(host='0.0.0.0', port=port, debug=debug) 