
#!/bin/bash

# Make sure logs directory exists
mkdir -p logs

# Start the application
echo "Starting application..."
python wsgi.py >> logs/production.log 2>&1
