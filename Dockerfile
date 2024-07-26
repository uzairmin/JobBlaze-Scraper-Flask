# start by pulling the python image
FROM python:3.10

RUN pip install --upgrade pip

WORKDIR /app

RUN apt-get update && apt-get install -y \
    wget \
    xvfb \
    libxi6 \
    libgconf-2-4 \
    default-jdk \
    libxslt-dev \
    libxml2 \
    libxml2-dev \
    libssl-dev \
    libffi-dev \
    libjpeg-dev \
    libxrender1 \
    xfonts-75dpi \
    xfonts-base \
    xauth \
    unzip \
    libnss3 \
    libgdk-pixbuf2.0-0 \
    fonts-liberation \
    gpg \
    ca-certificates \
    apt-transport-https \
    software-properties-common \
    && rm -rf /var/lib/apt/lists/*

# Install Google Chrome
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - && \
    echo "deb [arch=amd64] https://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list && \
    apt-get update && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# Install Chrome WebDriver
RUN wget -q https://chromedriver.storage.googleapis.com/LATEST_RELEASE -O /tmp/chromedriver_version && \
    wget -q https://chromedriver.storage.googleapis.com/$(cat /tmp/chromedriver_version)/chromedriver_linux64.zip -O /tmp/chromedriver.zip && \
    unzip /tmp/chromedriver.zip -d /usr/local/bin && \
    rm /tmp/chromedriver.zip && \
    chmod +x /usr/local/bin/chromedriver

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY . .

EXPOSE 8080

CMD ["flask", "run"]