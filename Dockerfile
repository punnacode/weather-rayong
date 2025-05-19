FROM python:3.10-slim

RUN apt-get update && apt-get install -y \
    wget unzip curl gnupg ca-certificates fonts-liberation libappindicator3-1 libasound2 \
    libatk-bridge2.0-0 libnspr4 libnss3 libxss1 xdg-utils \
    chromium chromium-driver && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

ENV CHROME_BIN=/usr/bin/chromium
ENV CHROMEDRIVER=/usr/bin/chromedriver

WORKDIR /app
COPY . .

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.port=10000", "--server.address=0.0.0.0"]
