
#!/bin/bash

# Production startup script with proper error handling and signal management

# Create logs directory if it doesn't exist
mkdir -p logs

# Log startup information
echo "$(date): Starting FiLot Bot in production mode" | tee -a logs/production.log

# Function to handle cleanup on exit
function cleanup() {
    echo "$(date): Shutting down gracefully..." | tee -a logs/production.log
    
    # Kill any other processes if needed
    if [ ! -z "$PID" ]; then
        echo "Stopping process $PID..." | tee -a logs/production.log
        kill -TERM $PID 2>/dev/null || true
    fi
    
    echo "$(date): Shutdown complete" | tee -a logs/production.log
    exit 0
}

# Set up signal handling
trap cleanup SIGINT SIGTERM

# Start the server and Telegram bot using wsgi.py
echo "$(date): Starting server and Telegram bot..." | tee -a logs/production.log

# Run with proper error handling
python wsgi.py 2>&1 | tee -a logs/production.log &
PID=$!

# Wait for the process to finish
wait $PID

# Check exit code
EXIT_CODE=$?
if [ $EXIT_CODE -ne 0 ]; then
    echo "$(date): Process exited with error code $EXIT_CODE" | tee -a logs/production.log
    echo "Check logs/production.log for details" | tee -a logs/production.log
else
    echo "$(date): Process completed successfully" | tee -a logs/production.log
fi

# Clean up before exit
cleanup
