#!/bin/bash

# Set the ChromeDriver version
CHROMEDRIVER_VERSION=114.0.5735.90

# Fetch the last known good versions with downloads
curl -s --insecure https://googlechromelabs.github.io/chrome-for-testing/last-known-good-versions-with-downloads.json -o /tmp/chrome_versions.json

# Display the contents of the fetched JSON
echo "Contents of /tmp/chrome_versions.json:"
cat /tmp/chrome_versions.json

# Extract the Chrome URL for mac64 platform
CHROME_URL=$(jq -r '.channels.Stable.downloads.chrome[] | select(.platform=="mac-x64") | .url' /tmp/chrome_versions.json)

# Extract the ChromeDriver URL for mac64 platform and the specified version
CHROMEDRIVER_URL=$(jq -r --arg VERSION "$CHROMEDRIVER_VERSION" '.channels.Stable.downloads.chromedriver[] | select(.platform=="mac-x64") | .url' /tmp/chrome_versions.json)

# Check if URLs were fetched successfully
if [ -z "$CHROME_URL" ] || [ -z "$CHROMEDRIVER_URL" ]; then
    echo "Failed to fetch Chrome or ChromeDriver URL";
    exit 1;
fi

# Display the fetched URLs
echo "Chrome URL: ${CHROME_URL}"
echo "Chrome Driver URL: ${CHROMEDRIVER_URL}"

# Download and install Chrome
echo "Downloading Chrome from $CHROME_URL"
curl -o /tmp/chrome-mac.zip -L $CHROME_URL
unzip -o /tmp/chrome-mac.zip -d /tmp
rm /tmp/chrome-mac.zip

# Move the Chrome app to the Applications folder
echo "Installing Chrome..."
if [ -d "/Applications/Google Chrome.app" ]; then
    rm -rf "/Applications/Google Chrome.app"
fi
mv /tmp/chrome-mac-x64/Google\ Chrome\ for\ Testing.app /Applications/Google\ Chrome.app

# Download and install ChromeDriver
echo "Downloading ChromeDriver from $CHROMEDRIVER_URL"
curl -o /tmp/chromedriver-mac.zip -L $CHROMEDRIVER_URL
unzip -o /tmp/chromedriver-mac.zip -d /usr/local/bin/
mv /usr/local/bin/chromedriver-mac-x64/chromedriver /usr/local/bin/chromedriver
rm -rf /tmp/chromedriver-mac.zip /usr/local/bin/chromedriver-mac-x64
chmod +x /usr/local/bin/chromedriver

# Verify installation
echo "Verifying Chrome installation..."
if [ -f "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome for Testing" ]; then
    echo "Chrome installed successfully."
else
    echo "Chrome installation failed."
    exit 1
fi

echo "Verifying ChromeDriver installation..."
if [ -f "/usr/local/bin/chromedriver" ]; then
    echo "ChromeDriver installed successfully."
else
    echo "ChromeDriver installation failed."
    exit 1
fi

echo "Chrome and ChromeDriver installed successfully."
