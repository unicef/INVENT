import os

import debugpy

# Only enable debugging if a specific environment variable is set
if os.getenv("ENABLE_DEBUGPY_FOR_UNIT_TESTS", "false").lower() == "true":
    print("Waiting for debugger to attach on port 5679...")
    debugpy.listen(("0.0.0.0", 5679))

    # Block execution until a debugger attaches
    debugpy.wait_for_client()
    print("Debugger attached!")