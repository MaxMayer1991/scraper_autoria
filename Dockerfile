FROM python:3.13-slim-bookworm

WORKDIR /app

# Об'єднуємо оновлення і встановлення тільки того, чого немає в базовому образі
# Базовий образ playwright вже має Python, pip, і купу ліб для браузера
RUN apt-get update && apt-get install -y \
    openssh-server \
    postgresql-client \
    tzdata \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Налаштування SSH
RUN mkdir -p /var/run/sshd && \
    echo 'root:root' | chpasswd && \
    sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config

# Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Playwright
RUN playwright install firefox
RUN playwright install-deps

COPY . .

EXPOSE 22

CMD service ssh start && python3 scheduler.py