#!/usr/bin/env python
import os
import sys


# Start the debugpy debugger if not already running
def start_debugger():
    try:
        from django.conf import (
            settings,  # Import settings after setting DJANGO_SETTINGS_MODULE
        )
        if settings.DEBUG:
            if os.environ.get('RUN_MAIN'): # Will only return true if this is the main process of djangos runserver
                import debugpy
                debugpy.listen(5678)
                print("Debugpy listening on port 5678")
    except ImportError:
        print("debugpy not installed or settings not configured. Skipping debug server setup.")

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tiip.settings")

    # Start debugger if needed
    start_debugger()

    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)