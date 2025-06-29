# Stage 1: Build SUMO
FROM ubuntu:22.04 AS builder

RUN apt-get update && apt-get install -y \
    git cmake g++ libxerces-c-dev libfox-1.6-dev libgdal-dev libproj-dev python3 python3-pip \
    && apt-get clean

RUN git clone https://github.com/eclipse/sumo.git /sumo-src && \
    cd /sumo-src && \
    git checkout v1_23_1 && \
    mkdir build && cd build && \
    cmake .. && make -j$(nproc) && make install

# Stage 2: Runtime environment
FROM ubuntu:22.04

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    python3 python3-pip libxerces-c3.2 libfox-1.6 libgdal30 libproj22 \
    && apt-get clean

# Copy SUMO binaries
COPY --from=builder /usr/local/bin/ /usr/local/bin/
COPY --from=builder /usr/local/share/sumo /usr/local/share/sumo

# Set up Python environment
WORKDIR /app
COPY requirements.txt /app/
RUN pip3 install -r requirements.txt

# Copy application code
COPY . /app

# Set SUMO_HOME for TraCI tools
ENV SUMO_HOME=/usr/local/share/sumo

CMD ["python3", "main.py"]
