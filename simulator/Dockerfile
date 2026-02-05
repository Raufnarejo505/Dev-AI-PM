FROM python:3.11-slim
WORKDIR /app
COPY *.py ./
RUN pip install --no-cache-dir paho-mqtt==2.1.0
CMD ["python", "publish_sim.py"]

