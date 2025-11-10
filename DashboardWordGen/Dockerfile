# --- Estágio 1: Builder ---
# Usamos uma imagem Python completa para instalar as dependências de forma eficiente.
FROM python:3.11-slim-buster as builder 

# Define o diretório de trabalho
WORKDIR /app

# Instala as dependências em um local separado para facilitar a cópia
RUN pip install --upgrade pip
COPY requirements.txt .
# --wheel-dir cria "wheels" pré-compilados, otimizando a instalação no próximo estágio.
RUN pip wheel --no-cache-dir --wheel-dir /app/wheels -r requirements.txt


# --- Estágio 2: Final ---
# Usamos uma imagem "slim" leve para a imagem final, reduzindo o tamanho.
FROM python:3.11-slim-bookworm 

# Define o diretório de trabalho dentro do contêiner
WORKDIR /app

# --- MUDANÇA PRINCIPAL: Instalar dependências como root ---
# Copia as dependências pré-compiladas do estágio de build.
COPY --from=builder /app/wheels /wheels
# Agora isso funcionará, pois estamos instalando wheels de 3.11 com um pip de 3.11
RUN pip install --no-cache /wheels/*

# Instala o curl, necessário para o HEALTHCHECK.
# É importante limpar o cache do apt para manter a imagem pequena.
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Copia todo o restante do código da aplicação para o contêiner.
# Copiamos o código APÓS instalar as dependências para aproveitar o cache do Docker.
COPY . .

# Cria um usuário não-root para executar a aplicação. É uma prática de segurança crucial.
RUN useradd --create-home appuser

# --- MUDANÇA PRINCIPAL: Mudar para o usuário não-root no final ---
# Mude para o usuário não-root DEPOIS que tudo estiver instalado e copiado.
USER appuser

# Expõe a porta que a aplicação vai usar.
EXPOSE 8501

# Adiciona uma verificação de saúde (HEALTHCHECK)
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
  CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# Comando para iniciar a aplicação.
CMD ["streamlit", "run", "Dashboard/app.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true","--server.enableCORS=false"]