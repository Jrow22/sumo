FROM ubuntu:22.04 AS builder
# Install dependencies
RUN apt-get update && apt-get install -y \
    git cmake g++ libxerces-c-dev libfox-1.6-dev libgdal-dev libproj-dev python3 python3-pip \
    && apt-get clean

RUN git clone https://github.com/eclipse/sumo.git /sumo-src && \
    cd /sumo-src && \
    git checkout v1_23_1 && \
    mkdir build && cd build && \
    cmake .. && make -j$(nproc) && make install

FROM python:3.11-slim-buster

WORKDIR /app

# Copy only requirements.txt first, so Docker caches this step unless requirements.txt changes
COPY requirements.txt /app/

COPY --from=builder /usr/local/bin/sumo /usr/local/bin/sumo
COPY --from=builder /usr/local/bin/netconvert /usr/local/bin/netconvert

RUN pip3 install -r requirements.txt  --verbose

# Then copy the rest of your app code
COPY . /app

ENV SUMO_HOME=/usr/local/share/sumo

CMD ["python3", "main.py"]
