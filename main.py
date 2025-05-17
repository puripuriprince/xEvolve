import json
import time
import uuid
import random
import os
from google import genai

# from evaluation import execute_evaluator

DATABASE_FILE = 'database.json'
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "YOUR_GEMINI_API_KEY")
gemini = genai.Client(api_key=GEMINI_API_KEY)
# --- Database Management ---

def initialize_database():
    """Initializes the database file if it doesn't exist."""
    if not os.path.exists(DATABASE_FILE):
        with open(DATABASE_FILE, 'w') as f:
            json.dump([], f)

def load_database():
    """Loads the database from the JSON file."""
    with open(DATABASE_FILE, 'r') as f:
        return json.load(f)

def save_database(db):
    """Saves the database to the JSON file."""
    with open(DATABASE_FILE, 'w') as f:
        json.dump(db, f, indent=4)

def add_to_database(child_program, results, parent_uuid=None, idea=""):
    """Adds a new program and its results to the database.
       [cite: 53, 54, 55, 56, 130, 131]
    """
    db = load_database()
    program_entry = {
        "uuid": str(uuid.uuid4()),
        "idea": idea,
        "program": child_program,
        "result": results,
        "parent_uuid": parent_uuid
    }
    db.append(program_entry)
    save_database(db)
    print(f"Added program {program_entry['uuid']} to the database.")
    return program_entry

def sample_from_database(num_samples=1, num_inspirations=2):
    """Samples a parent program and inspiration programs from the database.
       [cite: 53, 54]
    """
    db = load_database()
    if not db:
        print("Database is empty. Cannot sample.")
        # Return a default initial program if the database is empty
        initial_program = "# Initial empty program\ndef solve():\n    pass"
        return initial_program, []

    # For simplicity, we'll pick a random parent.
    # More sophisticated sampling (e.g., based on scores) can be implemented.
    # [cite: 131, 132, 133]
    parent_program_entry = random.choice(db)
    parent_program = parent_program_entry["program"]

    inspirations = []
    if len(db) > 1:
        # Exclude the parent program itself from inspirations
        potential_inspirations = [entry for entry in db if entry["uuid"] != parent_program_entry["uuid"]]
        if potential_inspirations:
            num_to_sample = min(num_inspirations, len(potential_inspirations))
            inspirations_entries = random.sample(potential_inspirations, num_to_sample)
            inspirations = [entry["program"] for entry in inspirations_entries]

    print(f"Sampled parent: {parent_program_entry['uuid']}")
    if inspirations:
        print(f"Sampled inspirations: {[entry['uuid'] for entry in inspirations_entries]}")
    return parent_program, inspirations

# --- LLM Interaction ---

def build_prompt(parent_program, inspirations):
    """Builds a prompt for the LLM based on the parent and inspiration programs.
       [cite: 53, 54, 74, 75, 76, 77, 78, 79, 80, 101]
    """
    prompt = "You are an expert programmer tasked with evolving code to solve a problem.\n"
    prompt += "Your goal is to suggest modifications (as a diff) to the 'Current program' to improve it.\n"
    prompt += "Consider the 'Prior programs' as inspiration for good ideas or approaches.\n\n"
    prompt += "The goal is to have a function `fib(n)` that returns the nth Fibonacci number.\n"

    if inspirations:
        prompt += "--- Prior programs (inspirations) ---\n"
        for i, insp_prog in enumerate(inspirations):
            prompt += f"Inspiration Program {i+1}:\n```python\n{insp_prog}\n```\n\n"
    else:
        prompt += "--- No Prior programs available for inspiration ---\n\n"

    prompt += "--- Current program (to be modified) ---\n"
    prompt += f"```python\n{parent_program}\n```\n\n"

    prompt += "--- Task ---\n"
    prompt += "Suggest a modification to the 'Current program'. \n"
    prompt += "Provide your suggested change in a diff format, like this:\n"
    prompt += "<<<<<<< SEARCH\n"
    prompt += "# Original code block to be found and replaced\n"
    prompt += "=======\n"
    prompt += "# New code block to replace the original\n"
    prompt += ">>>>>>> REPLACE\n\n"
    prompt += "If you are suggesting adding new code where nothing existed, "
    prompt += "the SEARCH block can be a comment indicating where to insert, "
    prompt += "or an adjacent line of code.\n"
    prompt += "If you are suggesting deleting code, the REPLACE block should be empty.\n"
    prompt += "Focus on a single, meaningful change. The change should be syntactically correct Python.\n"
    prompt += "Please provide only the diff block in your response. Do not provide any comments or codeblocks.\n"
    # Add more specific instructions based on the math/programming task if needed.
    prompt += "For example, if the current program is:\n"
    prompt += "```python\n# My Function\ndef my_func(x):\n    return x * 2\n```\n"
    prompt += "And you want to change it to `return x * 3`, the diff would be:\n"
    prompt += "<<<<<<< SEARCH\n    return x * 2\n=======\n    return x * 3\n>>>>>>> REPLACE\n"

    return prompt

def generate_with_llm(prompt):
    """Generates a code modification (diff) using the LLM.
       [cite: 53, 54, 55, 81, 106, 107, 108, 109]
    """
    response = gemini.models.generate_content(model="gemini-2.5-flash-preview-04-17", contents=prompt)
    diff = response.text
    return diff


# --- Program Modification ---

def apply_diff(parent_program, diff):
    """Applies the diff to the parent program to create a child program.
       [cite: 53, 55, 102, 106, 107, 108]
    """
    child_program = parent_program
    try:
        if "<<<<<<< SEARCH" not in diff or "=======" not in diff or ">>>>>>> REPLACE" not in diff:
            print("Warning: Diff format incorrect. Skipping application.")
            return parent_program # Return parent if diff is malformed

        parts = diff.split("=======")
        search_block = parts[0].replace("<<<<<<< SEARCH\n", "").rstrip()
        replace_block = parts[1].replace("\n>>>>>>> REPLACE", "").replace(">>>>>>> REPLACE", "").strip() # Handle cases with or without newline

        if search_block in child_program:
            child_program = child_program.replace(search_block, replace_block, 1)
            print("Diff applied successfully.")
        else:
            # Attempt to apply common cases like adding to an empty function
            if "pass" in search_block and "pass" in child_program:
                 child_program = child_program.replace("pass", replace_block, 1)
                 print("Diff applied by replacing 'pass'.")
            else:
                print("Warning: Search block not found in parent program. Diff not applied.")
                # Optionally, try to append if it's a completely new block and search was e.g. a comment
                # This part can be made more sophisticated.
                # For now, if exact search fails, we return the parent.
                return parent_program

    except Exception as e:
        print(f"Error applying diff: {e}")
        return parent_program # Return parent in case of error

    print(f"--- Child Program ---\n{child_program}\n---------------------")
    return child_program

# --- Evaluation ---

def execute_evaluator(child_program_str):
    """
    Executes the child program and returns the results.
    The user will fill in the specific evaluation logic.
    [cite: 53, 56]
    """
    print(f"Attempting to evaluate program:\n{child_program_str}")
    results = {
        "is_successful": False,
        "output_value": None,
        "time_taken": 0,
        "debug_logs": ""
    }
    try:
        start_time = time.time()
        
        temp_module = {}
        exec(child_program_str, temp_module)
        output = temp_module.get('fib', lambda: None)(20)
        results["output_value"] = output
        results["is_successful"] = (output == 6765)

        results["debug_logs"] = "Evaluation completed successfully."
        results["time_taken"] = time.time() - start_time
    except Exception as e:
        results["debug_logs"] = f"Error during evaluation: {str(e)}"
        results["is_successful"] = False
        results["time_taken"] = time.time() - start_time

    print(f"--- Evaluation Results ---\n{results}\n---------------------------------------")
    return results


# --- Main Evolution Loop ---
def evolution_loop(generations=5):
    """The core evolution loop. [cite: 54]"""
    initialize_database()

    # Add an initial seed program if the database is empty
    if not load_database():
        print("Database is empty. Adding an initial seed program.")
        initial_seed_program = """# Initial seed program
def solve():
    # This is a basic placeholder.
    # The LLM will try to improve this.
    return 0
"""
        initial_results = execute_evaluator(initial_seed_program)
        # Provide a placeholder "idea" for the initial seed
        add_to_database(initial_seed_program, initial_results, idea="Initial seed program")


    for i in range(generations):
        print(f"\n--- Generation {i+1} ---")

        parent_program_str, inspirations_strs = sample_from_database()
        current_parent_uuid = None
        # Find the UUID of the parent_program_str to pass to add_to_database
        db_for_uuid_lookup = load_database()
        for entry in db_for_uuid_lookup:
            if entry["program"] == parent_program_str:
                current_parent_uuid = entry["uuid"]
                break

        prompt = build_prompt(parent_program_str, inspirations_strs)
        diff = generate_with_llm(prompt)

        if not diff.strip(): # Check if diff is empty or whitespace
            print("LLM returned an empty diff. Skipping this generation.")
            continue

        child_program_str = apply_diff(parent_program_str, diff)

        # If apply_diff returned the parent due to an error or no change,
        # we might want to skip evaluation or handle it differently.
        if child_program_str == parent_program_str:
            print("Child program is identical to parent (diff might have failed or was no-op). Skipping full evaluation/add for this iteration.")
            # Optionally, you could add a penalty or simply not add it to DB.
            # For this example, we'll just print a message and continue.
            continue


        results = execute_evaluator(child_program_str)
        # The "idea" here could potentially be extracted from the LLM's reasoning if it provided one,
        # or a summary of the diff. For now, it's a placeholder.
        add_to_database(child_program_str, results, parent_uuid=current_parent_uuid, idea="LLM generated modification")

        print(f"--- End of Generation {i+1} ---")

if __name__ == "__main__":

    if GEMINI_API_KEY == "YOUR_GEMINI_API_KEY":
        print("Warning: GEMINI_API_KEY is not set. LLM calls will be simulated.")

    evolution_loop(generations=3)

    print("\nEvolution loop finished.")