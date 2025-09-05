import os
import subprocess
import argparse
import sys
import multiprocessing
from itertools import repeat

# Define the list of AI analysts
ANALYSTS = [
    "fundamentals_analyst",
    "investment_planner",
    "news_analyst",
    "risk_analyst",
    "social_media_analyst",
    "technical_analyst",
]

# Base directory for training scripts
TRAINING_BASE_DIR = "training"

def run_training_for_analyst(analyst_name, python_executable):
    """
    Runs the train.py script for a given analyst and returns its status and output.
    This function is designed to be called by a multiprocessing Pool.
    """
    log_header = f"--- Training for {analyst_name} ---"
    print(log_header) # Print start message immediately
    
    # Use the 'train_final.py' script for analysts that have been tuned, otherwise use the default 'train.py'
    script_name = "train_final.py" if analyst_name in ["risk_analyst", "fundamentals_analyst", "investment_planner", "news_analyst", "social_media_analyst"] else "train.py"
    train_script_path = os.path.join(TRAINING_BASE_DIR, analyst_name, script_name)

    if not os.path.exists(train_script_path):
        error_msg = f"Error: train.py not found for {analyst_name} at {train_script_path}"
        return (analyst_name, False, error_msg)

    command = [python_executable, train_script_path]

    try:
        process = subprocess.run(
            command, 
            capture_output=True, 
            text=True, 
            check=True, 
            encoding='utf-8', # Use utf-8 for better compatibility
            errors='replace'
        )
        output = f"{log_header}\nTraining completed successfully.\n"
        output += "\nSTDOUT:\n" + process.stdout
        if process.stderr:
            output += "\nSTDERR:\n" + process.stderr
        return (analyst_name, True, output)
    except subprocess.CalledProcessError as e:
        error_output = f"{log_header}\nError training {analyst_name}: Command returned non-zero exit status {e.returncode}.\n"
        error_output += "\nSTDOUT:\n" + e.stdout
        error_output += "\nSTDERR:\n" + e.stderr
        return (analyst_name, False, error_output)
    except Exception as e:
        error_output = f"{log_header}\nAn unexpected error occurred: {e}"
        return (analyst_name, False, error_output)

def main():
    parser = argparse.ArgumentParser(description="Run training for all AI analysts in parallel.")
    parser.add_argument(
        "--models-dir",
        help="Path to the root models directory (e.g., D:\\TradingAgents_AI_Cache\\models)",
        default=os.environ.get('TRADING_AGENTS_MODELS_DIR')
    )
    parser.add_argument(
        "--max-workers",
        type=int,
        help="Maximum number of parallel processes to run.",
        default=4 # Default to 4 parallel processes
    )
    args = parser.parse_args()

    models_dir = args.models_dir
    max_workers = args.max_workers

    # Determine the correct python executable from the virtual environment
    project_root = os.path.dirname(os.path.abspath(__file__))
    python_executable = os.path.join(project_root, ".venv", "Scripts", "python.exe")

    if not os.path.exists(python_executable):
        print(f"Error: Python executable not found at {python_executable}")
        python_executable = sys.executable
        print(f"Warning: Falling back to system python at {python_executable}.")

    if not models_dir:
        print("Error: Models directory not specified via --models-dir or TRADING_AGENTS_MODELS_DIR env var.")
        return
        
    # Set environment variables for the child processes
    os.environ['TRADING_AGENTS_MODELS_DIR'] = models_dir
    mlflow_tracking_uri = "file:///D:/TradingAgents_AI_Cache/mlruns"
    os.environ['MLFLOW_TRACKING_URI'] = mlflow_tracking_uri
    
    print("--- Starting Automated Parallel Training for all AI Analysts ---")
    print(f"Max parallel workers: {max_workers}")
    print(f"Using Python executable: {python_executable}")
    print(f"Using models directory: {models_dir}")
    print(f"Setting MLFLOW_TRACKING_URI to: {mlflow_tracking_uri}")

    # Prepare arguments for the pool
    tasks = zip(ANALYSTS, repeat(python_executable))

    # Create a multiprocessing pool and run the training tasks in parallel
    with multiprocessing.Pool(processes=max_workers) as pool:
        results = pool.starmap(run_training_for_analyst, tasks)

    print("\n--- All Training Processes Completed. Results: ---")
    
    all_successful = True
    for name, success, output in results:
        print("-" * 50)
        print(f"Result for: {name} - {"SUCCESS" if success else "FAILED"}")
        print(output)
        if not success:
            all_successful = False

    print("-" * 50)
    if all_successful:
        print("\n--- Automated training process completed successfully for all analysts. ---")
    else:
        print("\n--- Automated training process completed with one or more failures. ---")

if __name__ == "__main__":
    # Required for multiprocessing on some platforms (like Windows)
    multiprocessing.freeze_support()
    main()
