# Stage 1: Build Frontend React
FROM node:20-slim AS frontend-builder
WORKDIR /frontend

# Copy dependencies definitions
COPY dashboard-app/package*.json ./
RUN npm install

# Copy source code and build
COPY dashboard-app/ ./
RUN npm run build

# Stage 2: Backend & Google Chrome Environment
FROM python:3.12-slim

# Cài đặt các gói phụ thuộc cần thiết cho Google Chrome
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    curl \
    gnupg \
    unzip \
    ca-certificates \
    libglib2.0-0 \
    libnss3 \
    libgconf-2-4 \
    libfontconfig1 \
    libasound2 \
    libx11-xcb1 \
    libxcomposite1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxi6 \
    libxrandr2 \
    libxrender1 \
    libxss1 \
    libxtst6 \
    fonts-liberation \
    xdg-utils \
    procps \
    && rm -rf /var/lib/apt/lists/*

# Cài đặt Google Chrome Stable chính thức từ Google
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /usr/share/keyrings/google-chrome-keyring.gpg \
    && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google-chrome-keyring.gpg] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# Thiết lập user chuẩn cho Hugging Face Spaces (UID 1000)
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Cài đặt các thư viện Python
COPY --chown=user:user backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy toàn bộ code backend
COPY --chown=user:user backend /app/backend

# Copy bản build frontend từ Stage 1
COPY --chown=user:user --from=frontend-builder /frontend/dist /app/dashboard-app/dist

WORKDIR /app/backend

# Hugging Face Spaces yêu cầu mở cổng 7860
EXPOSE 7860

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]
