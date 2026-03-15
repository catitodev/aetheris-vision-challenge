# Dockerfile - Aetheris (Optimized for Cloud Run)
FROM python:3.12-slim

# 1. Instalar dependências de sistema (FFmpeg é obrigatório para áudio)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsm6 \
    libxext6 \
    && rm -rf /var/lib/apt/lists/*

# 2. Configurar diretório de trabalho
WORKDIR /app

# 3. Copiar apenas requirements primeiro (otimiza cache de build)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Copiar o código da aplicação
COPY . .

# 5. Expor a porta padrão do Cloud Run
EXPOSE 8080

# 6. Comando de inicialização (Gradio/FastRTC na porta 8080)
CMD ["python", "app.py"]
