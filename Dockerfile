FROM python:3.10

# Set environment variables to avoid dialog prompts
ENV DEBIAN_FRONTEND=noninteractive

# Install necessary apt-get packages
RUN apt-get update && apt-get install -y \
    libx11-xcb1 \
    libdbus-glib-1-2 \
    libgtk-3-0 \
    libxt6 \
    xvfb \
    wget \
    bzip2 \
    libxtst6 \
    libpci-dev \
    libasound2 \
    libnss3 \
    libxss1 \
    libappindicator3-1 \
    fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

# Download and install Firefox
RUN wget -O firefox.tar.bz2 "https://download.mozilla.org/?product=firefox-latest&os=linux64&lang=en-US" \
    && tar xjf firefox.tar.bz2 -C /opt/ \
    && ln -s /opt/firefox/firefox /usr/local/bin/firefox \
    && rm firefox.tar.bz2

# Set display port to avoid crash
RUN Xvfb :99 -ac &
ENV DISPLAY=:99

# Copy the current directory contents into the container
COPY . /app

# Set the working directory to /app
WORKDIR /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Make port 80 available to the world outside this container
EXPOSE 80

# Run app.py when the container launches
CMD ["python", "main.py"]

