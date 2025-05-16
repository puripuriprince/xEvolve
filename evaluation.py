import time



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
        output = temp_module.get('fib', lambda: None)(8) 
        results["output_value"] = output
        results["is_successful"] = (output == 21)
        results["debug_logs"] = "Evaluation completed successfully."
        results["time_taken"] = time.time() - start_time
    except Exception as e:
        results["debug_logs"] = f"Error during evaluation: {str(e)}"
        results["is_successful"] = False
        results["time_taken"] = time.time() - start_time

    print(f"--- Evaluation Results ---\n{results}\n---------------------------------------")
    return results
