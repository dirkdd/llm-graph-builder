#!/bin/bash
# Activation script for the Python environment

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install essential packages first
echo "Installing essential packages..."
pip install --upgrade pip
pip install pytest pytest-asyncio pandas

# Install project requirements
echo "Installing project requirements..."
pip install -r requirements.txt -c constraints.txt

# Verify installation
echo "Verifying installation..."
python -c "
try:
    import pytest
    import pandas
    import fastapi
    import neo4j
    import langchain
    print('✅ All core packages installed successfully!')
except ImportError as e:
    print(f'❌ Missing package: {e}')
"

echo "Environment setup complete!"
echo "To activate: source venv/bin/activate"