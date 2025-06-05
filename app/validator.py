# Validates solutions and model reasonableness.
import google.generativeai as genai
import logging
from nlp_processor import GEMINI_API_KEY

# Configure logging
logger = logging.getLogger(__name__)

# Configure Gemini API (already configured in app.py, but good to have as a fallback)
try:
    genai.configure(api_key=GEMINI_API_KEY)
except Exception as e:
    logger.error(f"Could not configure Gemini API in validator.py: {e}")

def perform_sanity_checks(model_representation: dict, solution: dict) -> list:
    """
    Performs sanity checks on the solution (e.g., constraint satisfaction, edge cases, units).
    Returns a list of issues found, or an empty list if all checks pass.
    """
    # TODO: Implement sanity checks.
    # - Constraint satisfaction: Check if solution variables satisfy all constraints.
    # - Edge cases: Test with extreme values if applicable.
    # - Units: If units are part of the model, check consistency (requires model to include unit info).
    print(f"Performing sanity checks (not yet implemented)...")
    issues = []
    # Example check (conceptual):
    # if not solution_satisfies_constraints(model_representation, solution):
    #     issues.append("Solution does not satisfy all constraints.")
    return issues

def check_model_reasonableness(model_representation: dict, solution: dict, problem_statement: str) -> str:
    """
    Uses Gemini API (via nlp_processor) to comment on model reasonableness
    and recommend sensitivity analysis if needed.
    """
    # This will likely call a function in nlp_processor.py
    # from . import nlp_processor # Assuming nlp_processor is in the same package
    # reasonableness_comment = nlp_processor.comment_on_reasonableness({"model": model_representation, "solution": solution, "problem": problem_statement})
    print(f"Checking model reasonableness (not yet implemented)...")
    return "Comments on reasonableness to be provided by Gemini API via nlp_processor."

def validate_execution_results(problem_statement: str, model_plaintext: str, python_code: str, execution_output: str, api_key: str = None) -> dict:
    """
    Uses Gemini API to validate the optimization model results.
    
    Args:
        problem_statement: The original problem statement
        model_plaintext: The mathematical model 
        python_code: The PuLP code used
        execution_output: The output from running the code
        api_key: Optional API key to use instead of global configuration
        
    Returns:
        dict: A dictionary containing validation results, including:
            'is_valid': Boolean indicating if results are valid
            'assessment': Detailed assessment of the results
            'suggestions': Suggestions for improving the model if needed
            'confidence': Confidence level in the validation (high, medium, low)
            'explanation': Overall explanation of the results in user-friendly terms
    """
    logger.info("Validating optimization model results with Gemini...")
    
    try:
        # Create a prompt for Gemini to analyze the results
        prompt = f"""
You are an expert Operations Research validator. Provide a CONCISE analysis of the following optimization problem and solution.

PROBLEM STATEMENT:
{problem_statement}

MATHEMATICAL MODEL:
{model_plaintext}

PYTHON CODE USED:
```python
{python_code}
```

EXECUTION OUTPUT:
```
{execution_output}
```

Your task is to verify the solution's validity in a BRIEF and INSIGHTFUL manner. Limit your analysis to the most important aspects.

Provide a short analysis with exactly the following structure, keeping each section to 3-5 sentences maximum:

1. VALIDITY ASSESSMENT: A single sentence stating if the solution is valid (Yes/No/Partially).

2. CONSTRAINT VERIFICATION: Verify key constraints ONLY - check if they are satisfied by the solution values. Include only the most important calculations. Use a compact tabular format where appropriate.

3. PRACTICAL REASONABLENESS: In 2-3 sentences, evaluate if the solution makes sense in real-world terms and for stakeholders.

4. SUGGESTIONS: If there are issues, provide 1-3 specific, actionable suggestions. Otherwise, state "No suggestions needed."

5. CONFIDENCE LEVEL: One sentence - high, medium, or low confidence with brief justification.

Keep your ENTIRE response under 500 words. Prioritize clarity and precision over length. Focus on the most critical insights only. Use bullet points and short sentences.
"""

        # Configure API key if provided
        if api_key:
            genai.configure(api_key=api_key)
            
        # Call Gemini API
        generation_config = {
            "temperature": 0.2,
            "top_p": 0.9,
            "top_k": 40,
            "max_output_tokens": 8192,
        }
        
        model = genai.GenerativeModel(
            model_name="gemini-2.0-flash-exp",
            generation_config=generation_config
        )
        
        logger.info("Sending validation request to Gemini API...")
        response = model.generate_content(prompt)
        
        if hasattr(response, 'text') and response.text:
            analysis_text = response.text
            logger.info("Received validation analysis from Gemini.")
            
            # Parse the AI response into structured components
            # This is a simplified parsing approach - in production you might want
            # to use a more robust approach or structured output format from the API
            sections = {
                "validity": "Valid",
                "constraints": "",
                "reasonableness": "",
                "suggestions": "",
                "confidence": "Medium"  # Default if not found
            }
            
            # Extract sections from text
            if "VALIDITY ASSESSMENT" in analysis_text:
                validity_section = analysis_text.split("VALIDITY ASSESSMENT:")[1].split("\n\n")[0].strip()
                if "yes" in validity_section.lower():
                    sections["validity"] = "Valid"
                elif "no" in validity_section.lower():
                    sections["validity"] = "Invalid"
                elif "partial" in validity_section.lower():
                    sections["validity"] = "Partially Valid"
            
            # Extract constraint verification    
            if "CONSTRAINT VERIFICATION" in analysis_text and "PRACTICAL REASONABLENESS" in analysis_text:
                try:
                    sections["constraints"] = analysis_text.split("CONSTRAINT VERIFICATION:")[1].split("PRACTICAL REASONABLENESS:")[0].strip()
                except:
                    sections["constraints"] = "Constraint verification not available."
                
            # Extract practical reasonableness
            if "PRACTICAL REASONABLENESS" in analysis_text and "SUGGESTIONS" in analysis_text:
                try:
                    sections["reasonableness"] = analysis_text.split("PRACTICAL REASONABLENESS:")[1].split("SUGGESTIONS:")[0].strip()
                except:
                    sections["reasonableness"] = "Practical reasonableness assessment not available."
                    
            if "SUGGESTIONS" in analysis_text:
                try:
                    sections["suggestions"] = analysis_text.split("SUGGESTIONS:")[1].split("CONFIDENCE LEVEL")[0].strip()
                    if "no suggestions needed" in sections["suggestions"].lower():
                        sections["suggestions"] = "No suggestions needed."
                except:
                    sections["suggestions"] = "No specific suggestions provided."
                    
            if "CONFIDENCE LEVEL" in analysis_text:
                confidence_section = analysis_text.split("CONFIDENCE LEVEL:")[1].strip().split("\n\n")[0].lower()
                if "high" in confidence_section:
                    sections["confidence"] = "High"
                elif "medium" in confidence_section:
                    sections["confidence"] = "Medium"
                elif "low" in confidence_section:
                    sections["confidence"] = "Low"
            
            # Create the result dictionary
            result = {
                "is_valid": sections["validity"] == "Valid",
                "validity_status": sections["validity"],
                "constraint_verification": sections["constraints"],
                "practical_reasonableness": sections["reasonableness"],
                "suggestions": sections["suggestions"],
                "confidence": sections["confidence"],
                "full_analysis": analysis_text  # Include the full text as well
            }
            
            return result
        else:
            logger.warning("Gemini response for validation does not contain text or is empty.")
            return {
                "is_valid": False,
                "validity_status": "Unknown",
                "assessment": "The AI validator could not analyze the results. This may be due to issues with the execution output format or content filtering.",
                "suggestions": "Try simplifying your model or providing more structured output.",
                "confidence": "Low",
                "full_analysis": "No analysis generated."
            }
            
    except Exception as e:
        logger.error(f"Exception during validation: {e}", exc_info=True)
        return {
            "is_valid": False,
            "validity_status": "Error",
            "assessment": f"An error occurred during validation: {str(e)}",
            "suggestions": "Please check server logs for more details.",
            "confidence": "None",
            "full_analysis": f"Error: {str(e)}"
        } 