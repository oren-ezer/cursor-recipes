#!/usr/bin/env python
"""
Script to run Alembic migrations with environment variables from .env file.
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv("backend/.env")

# Verify that DATABASE_URL is set
if not os.getenv("DATABASE_URL"):
    raise ValueError("DATABASE_URL environment variable is not set. Please set it to your Supabase connection URL.")

# Run Alembic command
if __name__ == "__main__":
    from alembic.config import Config
    from alembic import command
    
    # Create Alembic configuration
    alembic_cfg = Config("alembic.ini")
    
    # Run the command passed as arguments
    if len(sys.argv) > 1:
        command_name = sys.argv[1]
        command_args = sys.argv[2:]
        
        # Get the command function
        cmd_func = getattr(command, command_name)
        
        # Run the command
        if command_name == "revision" and "--autogenerate" in command_args:
            # For autogenerate, we need to pass the arguments as keyword arguments
            kwargs = {}
            for i, arg in enumerate(command_args):
                if arg.startswith("--"):
                    if i + 1 < len(command_args) and not command_args[i + 1].startswith("--"):
                        kwargs[arg[2:]] = command_args[i + 1]
                    else:
                        kwargs[arg[2:]] = True
            cmd_func(alembic_cfg, **kwargs)
        else:
            # For other commands, pass the arguments as positional arguments
            cmd_func(alembic_cfg, *command_args)
    else:
        print("Usage: python run_migrations.py <command> [args...]")
        print("Example: python run_migrations.py revision --autogenerate -m 'Create users table'")
        print("Example: python run_migrations.py upgrade head") 