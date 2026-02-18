import os
import time
import logging

# Define a path that all Gunicorn workers can access and write to
# A path in the application directory or /tmp/ is common
SENTINEL_FILE = 'gunicorn_one_time_init.lock'

def run_once_with_sentinel(func_run):
    """Checks for a file, runs the function, and creates the file if it's missing."""

    # 1. Check if the file exists
    if os.path.exists(SENTINEL_FILE):
        logging.info(f"PID {os.getpid()} skipped function: Sentinel file already exists.")
        return False

    # 2. If it does NOT exist, create the file and run the function
    try:
        # Crucial step: Create the file. The 'x' mode ensures the file is created
        # ONLY if it does not already exist. If two processes try to create it
        # at the same exact time, only one will succeed (atomic operation).
        with open(SENTINEL_FILE, 'x') as f:
            f.write(f"Initialized by PID {os.getpid()} at {time.ctime()}\n")

        # --- EXECUTE YOUR FUNCTION HERE ---
        logging.info(f"PID {os.getpid()} is the first and is running the one-time setup...")
        # Your actual one-time setup code goes here (e.g., database initialization)
        # ---------------------------------
        time.sleep(5)
        os.remove(SENTINEL_FILE) # allows workers to negotiate who runs file
        func_run()
        logging.info("One-time setup complete.")
        return True

    except FileExistsError:
        # This catches the scenario where another worker process created the
        # file in the instant between os.path.exists() and open(..., 'x').
        logging.info(f"PID {os.getpid()} failed atomic check; another process just created the file.")
        return False
    except Exception as e:
        # Handle other errors, and ensure the sentinel file is cleaned up if the
        # function fails *during* initialization (optional but good practice)
        if os.path.exists(SENTINEL_FILE):
             os.remove(SENTINEL_FILE)
        raise e
