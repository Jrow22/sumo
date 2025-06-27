FROM ubuntu:22.04

# Install dependencies
RUN apt-get update && apt-get install -y \
    git cmake g++ libxerces-c-dev libfox-1.6-dev libgdal-dev libproj-dev python3 python3-pip \
    && apt-get clean

RUN git clone https://github.com/eclipse/sumo.git /sumo-src && \
    cd /sumo-src && \
    git checkout v1_18_0 && \
    mkdir build && cd build && \
    cmake .. && make -j$(nproc) && make install

ENV SUMO_HOME=/usr/local/share/sumo

WORKDIR /app

# Copy only requirements.txt first, so Docker caches this step unless requirements.txt changes
COPY requirements.txt /app/

RUN pip3 install --no-cache-dir -r requirements.txt

# Then copy the rest of your app code
COPY . /app

CMD ["python3", "main.py"]
