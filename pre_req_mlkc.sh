#!/bin/bash

# Function to install packages for Debian-based systems
install_packages_debian() {
    sudo apt-get update
    sudo apt-get install -y git python3 python3-pip
}

# Function to install packages for RPM-based systems
install_packages_rpm() {
    sudo yum install -y git python3 python3-pip
}

# Function to install packages for Amazon Linux
install_packages_amzn() {
    sudo yum install -y git
    sudo yum install -y python3
    sudo yum install -y python3-pip
}

# Function to check if a package is installed
is_installed() {
    command -v "$1" >/dev/null 2>&1
}

# Check if the OS is Debian-based, RPM-based, or Amazon Linux
if [[ -e /etc/os-release ]]; then
    source /etc/os-release
    if [[ $ID == "debian" || $ID == "ubuntu" || $ID == "linuxmint" ]]; then
        echo "Detected Debian-based or Ubuntu OS."
        install_packages_debian
    elif [[ $ID == "centos" || $ID == "rhel" ]]; then
        echo "Detected RPM-based OS."
        install_packages_rpm
    elif [[ $ID == "amzn" ]]; then
        echo "Detected Amazon Linux."
        install_packages_amzn
    else
        echo "Unsupported operating system: $ID"
        exit 1
    fi
else
    echo "Unable to determine the operating system."
    exit 1
fi

# Check if Git is installed, and install it if not
if ! is_installed git; then
    echo "Git is not installed. Installing Git..."
    install_packages_"$ID"
    echo "Git installed successfully."
else
    echo "Git is already installed."
fi

# Check if Python3 is installed, and install it if not
if ! is_installed python3; then
    echo "Python3 is not installed. Installing Python3..."
    install_packages_"$ID"
    echo "Python3 installed successfully."
else
    echo "Python3 is already installed."
fi

# Check if pip3 is installed, and install it if not
if ! is_installed pip3; then
    echo "pip3 is not installed. Installing pip3..."
    install_packages_"$ID"
    echo "pip3 installed successfully."
else
    echo "pip3 is already installed."
fi

echo "🔍 Detecting package manager..."
if command -v apt >/dev/null 2>&1; then
    PKG_MGR="apt"
    PYTHON_VENV_PKG="python3-venv"
    
elif command -v yum >/dev/null 2>&1; then
    PKG_MGR="yum"
    PYTHON_VENV_PKG="python3-venv"  # Might be in python3 module
    
elif command -v dnf >/dev/null 2>&1; then
    PKG_MGR="dnf"
    PYTHON_VENV_PKG="python3-venv"
    
else
    echo "❌ Unsupported OS: no apt, yum, or dnf found."
    exit 1
fi

echo "✅ Using package manager: $PKG_MGR"

# Install required packages
if [ "$PKG_MGR" = "apt" ]; then
    echo "🔍 Checking if python3-venv is installed..."
    if ! dpkg -s python3-venv >/dev/null 2>&1; then
        echo "⚠️  python3-venv not found. Installing..."
        sudo apt update -y
        sudo apt install -y  $PYTHON_VENV_PKG
    else
        echo "✅ python3-venv is already installed."
    fi
else
    echo "🔍 Installing Python venv and Docker..."
    sudo $PKG_MGR install -y python3 python3-pip python3-virtualenv || \
    sudo $PKG_MGR install -y python3 python3-pip python3-venv
fi

# Create virtual environment if missing
VENV_DIR="venv"
ACTIVATE="$VENV_DIR/bin/activate"

if [ ! -f "$ACTIVATE" ]; then
    echo "📦 (Re)creating virtual environment in $VENV_DIR..."
    rm -rf "$VENV_DIR"
    python3 -m venv "$VENV_DIR"
    echo "✅ Virtual environment created."
else
    echo "✅ Virtual environment already exists."
fi

# Activate virtual environment
echo "🐍 Activating virtual environment..."
source "$ACTIVATE"

# Install requirements
if [ -f "requirements.txt" ]; then
    echo "📦 Installing Python packages from requirements.txt..."
    pip install --upgrade pip
    pip install -r requirements.txt
    echo "✅ Python packages installed."
else
    echo "❌ requirements.txt not found!"
    exit 1
fi

# Run Python app
echo "🚀 Running mlkc.py..."
python3 mlkc.py
