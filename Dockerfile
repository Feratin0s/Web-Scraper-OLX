FROM python:3.9-slim

# Instala o Google Chrome
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    xvfb \
    libxi6 \
    && wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /usr/share/keyrings/google-chrome.gpg \
    && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google-chrome.gpg] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Define o diretório de trabalho
WORKDIR /app

# Copia os arquivos necessários
COPY requirements.txt .
COPY scraper.py .
COPY .env .

# Instala as dependências
RUN pip install --no-cache-dir -r requirements.txt

# Configuração para desabilitar o buffer de saída
ENV PYTHONUNBUFFERED=1

# Define a variável de ambiente para indicar que está rodando em Docker
ENV DOCKER_ENV=true

# Comando para executar o script
CMD ["python", "scraper.py"]