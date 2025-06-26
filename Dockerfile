FROM ubuntu:22.04

# Install dependencies
RUN apt-get update && apt-get install -y \
    python3 python3-pip \
    sumo sumo-tools \
    && apt-get clean

ENV SUMO_HOME=/usr/share/sumo

WORKDIR /app

# Copy only requirements.txt first, so Docker caches this step unless requirements.txt changes
COPY requirements.txt /app/

RUN pip3 install --no-cache-dir -r requirements.txt

# Then copy the rest of your app code
COPY . /app

CMD ["python3", "main.py"]
