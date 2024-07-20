#!/bin/bash

# Define the paths for Chrome and ChromeDriver
CHROME_PATH="/Applications/chrome-mac-x64/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing"
CHROMEDRIVER_PATH="/usr/local/bin/chromedriver"

# Install jq if not already installed
if ! command -v jq &> /dev/null
then
    echo "jq could not be found, installing..."
    brew install jq
fi

# Download and install Google Chrome
echo "Downloading and installing Google Chrome..."
CHROME_URL=$(curl -s https://googlechromelabs.github.io/chrome-for-testing/last-known-good-versions-with-downloads.json | jq -r '.channels.Stable.downloads.chrome[] | select(.platform=="mac-x64") | .url')
curl -o /tmp/chrome-mac.zip -L $CHROME_URL
unzip -o /tmp/chrome-mac.zip -d /Applications
rm /tmp/chrome-mac.zip

# Verify Chrome installation
if [ ! -f "$CHROME_PATH" ]; then
  echo "Google Chrome installation failed."
  exit 1
else
  echo "Google Chrome installed successfully."
fi

# Download and install ChromeDriver
echo "Downloading and installing ChromeDriver..."
CHROMEDRIVER_URL=$(curl -s https://googlechromelabs.github.io/chrome-for-testing/last-known-good-versions-with-downloads.json | jq -r '.channels.Stable.downloads.chromedriver[] | select(.platform=="mac-x64") | .url')
curl -o /tmp/chromedriver-mac.zip -L $CHROMEDRIVER_URL
unzip -o /tmp/chromedriver-mac.zip -d /tmp
mv /tmp/chromedriver-mac-x64/chromedriver /usr/local/bin/chromedriver
rm -rf /tmp/chromedriver-mac.zip /tmp/chromedriver-mac-x64
chmod +x /usr/local/bin/chromedriver

# Verify ChromeDriver installation
if [ ! -f "$CHROMEDRIVER_PATH" ]; then
  echo "ChromeDriver installation failed."
  exit 1
else
  echo "ChromeDriver installed successfully."
fi

# Set up environment variables in Conda activation script
echo "Setting up environment variables for Conda..."
CONDA_ENV_PATH="/opt/anaconda3/envs/grainger_recommendations_chatbot_3-11"
ACTIVATE_SCRIPT="$CONDA_ENV_PATH/etc/conda/activate.d/env_vars.sh"

mkdir -p "$CONDA_ENV_PATH/etc/conda/activate.d"
touch "$ACTIVATE_SCRIPT"

echo '#!/bin/bash' > "$ACTIVATE_SCRIPT"
echo "export CHROME_BINARY_PATH=\"$CHROME_PATH\"" >> "$ACTIVATE_SCRIPT"
echo "export PATH=\"/usr/local/bin:\$PATH\"" >> "$ACTIVATE_SCRIPT"

chmod +x "$ACTIVATE_SCRIPT"

echo "Installation and setup completed successfully."
