FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive

# -----------------------------------------------------
# Install system dependencies
# -----------------------------------------------------
RUN apt-get update && apt-get install -y \
    gnupg \
    curl \
    wget \
    unzip \
    --no-install-recommends

# -----------------------------------------------------
# Add Google Chrome repository and install Chrome
# -----------------------------------------------------
RUN curl -fsSL https://dl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /usr/share/keyrings/googlechrome.gpg \
    && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/googlechrome.gpg] http://dl.google.com/linux/chrome/deb/ stable main" \
       > /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable

# -----------------------------------------------------
# Install matching ChromeDriver
# -----------------------------------------------------
RUN CHROME_VERSION=$(google-chrome --version | sed 's/Google Chrome //') \
    && CHROME_MAJOR=$(echo $CHROME_VERSION | cut -d '.' -f 1) \
    && wget -q "https://chromedriver.storage.googleapis.com/LATEST_RELEASE_$CHROME_MAJOR" -O /tmp/version \
    && DRIVER_VERSION=$(cat /tmp/version) \
    && wget -q "https://chromedriver.storage.googleapis.com/$DRIVER_VERSION/chromedriver_linux64.zip" \
    && unzip chromedriver_linux64.zip -d /usr/local/bin/ \
    && chmod +x /usr/local/bin/chromedriver \
    && rm chromedriver_linux64.zip

# -----------------------------------------------------
# Create non-root Selenium user
# -----------------------------------------------------
RUN useradd -m seluser
USER seluser

WORKDIR /app

# -----------------------------------------------------
# Python dependencies
# -----------------------------------------------------
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["gunicorn", "-b", "0.0.0.0:8080", "app:app"]
