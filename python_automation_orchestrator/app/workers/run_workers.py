"""
Worker runner script for the orchestrator application.

This script starts all background workers for the application.
"""

import asyncio
import logging
import signal
import sys
import os

from ..utils.logging import setup_logging
from . import start_workers, stop_workers

# Set up logging
logger = setup_logging()

async def main():
    """Main function to run all workers"""
    try:
        # Start all workers
        start_workers()
        
        # Keep running until interrupted
        while True:
            await asyncio.sleep(1)
            
    except asyncio.CancelledError:
        logger.info("Workers cancelled")
        
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        
    finally:
        # Stop all workers
        await stop_workers()
        
        logger.info("Workers runner stopped")

def signal_handler(sig, frame):
    """Handle signals to gracefully shut down"""
    logger.info(f"Received signal {sig}")
    # Raise KeyboardInterrupt to trigger graceful shutdown
    raise KeyboardInterrupt()

if __name__ == "__main__":
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    logger.info("Starting worker processes")
    
    # Run the main function
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Shutting down workers...")
    except Exception as e:
        logger.exception(f"Error in worker process: {e}")
        sys.exit(1)
    
    logger.info("Worker processes terminated")
    sys.exit(0)