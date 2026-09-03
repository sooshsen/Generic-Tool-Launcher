#!/bin/bash

set -e

# always run from directory containing this script
cd "$(dirname "$0")"

ENV_NAME="tool-launcher"

echo "---------------------------------"
echo "Generic Tool Launcher - Setup"
echo "---------------------------------"
echo

# -------------------------
# Check Conda
# -------------------------

if ! command -v conda &> /dev/null; then
	echo "ERROR: Conda not found."
	echo 
	echo "Please install Miniconda/Anaconda first."
	exit 1
fi

echo "Conda found:"
conda --version
echo

# ------------------------------
# Check if environment exists
# ------------------------------

echo "Checking for Conda environment '$ENV_NAME'..."

if conda env list | grep -qE "^[[:space:]]*$ENV_NAME[[:space:]]"; then
	echo "Environment already exists."
else
	echo "Environment does not exist."
	echo "Creating environment '$ENV_NAME'..."

	conda create -n "$ENV_NAME" python=3.12 -y

	echo "Environment created successfully."
fi

echo

# -------------------------
# Upgrade pip
# -------------------------

echo "Upgrading pip..."
conda run -n "$ENV_NAME" python -m pip install --upgrade pip

echo

# -------------------------
# Install requirements
# -------------------------

echo "Installing Python dependencies..."
conda run -n "$ENV_NAME" python -m pip install -r requirements.txt

echo

# -----------------------------
# Verify PySide6 installation
# -----------------------------

echo "---------------------------------"
echo "Checking PySide6 installation"
echo "---------------------------------"
echo

echo "Checking QtCore..."
conda run -n "$ENV_NAME" python -c \
"from PySide6 import QtCore; print('QtCore OK - version:', QtCore.__version__)"

echo

echo "Checking QtWidgets..."
conda run -n "$ENV_NAME" python -c \
"from PySide6 import QtWidgets; print('QtWidgets OK')"

echo


# ---------------
# Start GUI
# ---------------

echo "---------------------------------"
echo "All checks passed!"
echo "---------------------------------"
echo
echo "Starting Generic Tool Launcher GUI..."
echo

conda run -n "$ENV_NAME" python -m app.main