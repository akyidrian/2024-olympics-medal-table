FROM python:3.12

# Set environment variables to avoid dialog prompts
ENV DEBIAN_FRONTEND=noninteractive

# Install necessary apt-get packages
RUN apt-get update && apt-get install -y \
    libx11-xcb1 \
    libdbus-glib-1-2 \
    libgtk-3-0 \
    libxt6 \
    wget \
    bzip2 \
    libxtst6 \
    libasound2 \
    libnss3 \
    libxss1 \
    fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

# Download and install Firefox
RUN wget -O firefox.tar.bz2 "https://download.mozilla.org/?product=firefox-latest&os=linux64&lang=en-US" \
    && tar xjf firefox.tar.bz2 -C /opt/ \
    && ln -s /opt/firefox/firefox /usr/local/bin/firefox \
    && rm firefox.tar.bz2

# Copy app files, install requirements and run
COPY . /app
WORKDIR /app
RUN pip install --no-cache-dir -r requirements.txt
CMD ["python", "main.py"]

