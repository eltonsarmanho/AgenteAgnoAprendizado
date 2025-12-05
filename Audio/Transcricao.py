import time
import os
import google.generativeai as genai
from dotenv import load_dotenv
from agno.agent import Agent
from agno.models.google import Gemini

load_dotenv(override=True)

google_api_key = os.getenv("GOOGLE_API_KEY")
if not google_api_key:
    raise ValueError("GOOGLE_API_KEY e obrigatoria")

# 1. Configurar API e fazer Upload (Necessário para arquivos > 20MB)
genai.configure(api_key=google_api_key)
audio_path = "/home/eltonss/Documents/VS CODE/AgenteAgnoAprendizado/Audio/Forum.mp3"

print(f"Fazendo upload do arquivo: {audio_path}")
try:
    # Upload do arquivo
    audio_file = genai.upload_file(path=audio_path)
    print(f"Upload iniciado: {audio_file.name}")
    
    # Aguardar processamento
    while audio_file.state.name == "PROCESSING":
        print(".", end="", flush=True)
        time.sleep(2)
        audio_file = genai.get_file(audio_file.name)
    
    if audio_file.state.name == "FAILED":
        raise ValueError(f"Falha no processamento: {audio_file.state.name}")
    print(f"\nArquivo pronto! URI: {audio_file.uri}")

except Exception as e:
    print(f"Erro no upload: {e}")
    raise

# 2. Configurar o Agente Agno
agent = Agent(
    model=Gemini(id="gemini-2.0-flash", api_key=google_api_key),
    markdown=True
)

prompt_text = """Faça uma análise completa deste áudio de reunião e gere um relatório detalhado contendo:
1. RESUMO EXECUTIVO
2. PRINCIPAIS PONTOS DISCUTIDOS
3. DECISÕES TOMADAS
4. RECOMENDAÇÕES
5. SUGESTÕES
6. ALERTAS E PREOCUPAÇÕES
7. PRÓXIMOS PASSOS / AÇÕES
"""

print("\nGerando análise com Agno...")

# 3. Construir a mensagem manualmente para o Agno
# Isso garante que o file_uri seja passado corretamente para o Gemini
# sem tentar converter o arquivo local para base64
message_content = [
    {"type": "text", "text": prompt_text},
    {
        "type": "file_url", 
        "file_url": {
            "url": audio_file.uri, 
            # O Gemini precisa saber que é um arquivo de áudio via file_data, 
            # mas o Agno pode abstrair isso. Se falhar, usamos a estrutura raw abaixo.
        }
    }
]

# TENTATIVA ROBUSTA: Passar a estrutura exata que o Gemini espera dentro da lista de mensagens
# O Agno geralmente repassa dicionários desconhecidos ou estruturados para o modelo.
gemini_message = {
    "role": "user",
    "parts": [
        {"file_data": {"mime_type": "audio/mp3", "file_uri": audio_file.uri}},
        {"text": prompt_text}
    ]
}

# Executar o agente passando a mensagem estruturada
# Nota: Dependendo da versão do Agno, ele pode aceitar 'messages' ou exigir adaptação.
# Vamos tentar passar o conteúdo diretamente se o Agno permitir inputs complexos.

try:
    # Método A: Tentar passar a mensagem estruturada (funciona se o Agno repassar para o SDK)
    agent.print_response(messages=[gemini_message], stream=True)
except Exception:
    # Método B: Fallback usando a biblioteca nativa mas mantendo a estrutura do código
    print("Agno encontrou dificuldade com o formato da mensagem, usando fallback direto...")
    model = genai.GenerativeModel("gemini-2.0-flash")
    response = model.generate_content([audio_file, prompt_text], stream=True)
    for chunk in response:
        print(chunk.text, end="", flush=True)