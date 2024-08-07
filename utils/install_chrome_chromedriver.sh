#!/bin/bash

set -e

# Define URLs
CHROME_URL="https://storage.googleapis.com/chrome-for-testing-public/127.0.6533.99/mac-x64/chrome-mac-x64.zip"
CHROMEDRIVER_URL="https://storage.googleapis.com/chrome-for-testing-public/127.0.6533.99/mac-x64/chromedriver-mac-x64.zip"

# Download Chrome
echo "Downloading Chrome from $CHROME_URL"
curl -o /tmp/chrome-mac.zip -L $CHROME_URL

# Unzip Chrome
echo "Unzipping Chrome"
unzip -o /tmp/chrome-mac.zip -d /tmp

# Check if the application directory already exists and remove it
if [ -d "/Applications/Google Chrome for Testing.app" ]; then
    echo "Removing existing /Applications/Google Chrome for Testing.app"
    sudo rm -rf "/Applications/Google Chrome for Testing.app"
fi

# Move Chrome to Applications
echo "Moving Chrome to /Applications"
sudo mv /tmp/chrome-mac-x64/Google\ Chrome\ for\ Testing.app /Applications/Google\ Chrome\ for\ Testing.app

# Ensure the default Chrome directory exists
echo "Ensuring the default Chrome directory exists"
if [ ! -d "/Applications/Google Chrome.app/Contents/MacOS" ]; then
    echo "Creating directory /Applications/Google Chrome.app/Contents/MacOS"
    sudo mkdir -p "/Applications/Google Chrome.app/Contents/MacOS"
fi

# Replace default Chrome binary
echo "Replacing default Chrome binary"
sudo mv "/Applications/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing" "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

# Download ChromeDriver
echo "Downloading ChromeDriver from $CHROMEDRIVER_URL"
curl -o /tmp/chromedriver-mac.zip -L $CHROMEDRIVER_URL

# Unzip ChromeDriver
echo "Unzipping ChromeDriver"
unzip -o /tmp/chromedriver-mac.zip -d /tmp

# Move ChromeDriver to /usr/local/bin
echo "Moving ChromeDriver to /usr/local/bin"
sudo mv /tmp/chromedriver-mac-x64/chromedriver /usr/local/bin/
sudo chmod +x /usr/local/bin/chromedriver

# Verify installation
echo "Verifying Chrome installation"
if [ -f "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" ]; then
    echo "Chrome for Testing installed successfully"
else
    echo "Chrome for Testing installation failed"
    exit 1
fi

echo "Verifying ChromeDriver installation"
if command -v chromedriver &> /dev/null; then
    echo "ChromeDriver installed successfully"
else
    echo "ChromeDriver installation failed"
    exit 1
fi

echo "Installation completed successfully"

# chmod +x utils/install_chrome_chromedriver.sh
  # ./utils/install_chrome_chromedriver.sh
