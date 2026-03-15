# Aetheris — Assistente Cognitivo Multimodal

Resumo curto (one-liner): Aetheris transforma prints e fotos em descrições e ações por voz — assistente de acessibilidade e suporte técnico.

Status: MVP — Snapshot-to-Voice. Deploy: Cloud Run (em testes).

## Principais features (MVP)
- Upload de imagem (print/foto) como contexto
- Interação por voz (VAD, envio on-pause)
- Gemini Live (audio response)
- Arquitetura pronta para evoluir para live video com TURN/Cloud Run

## Como rodar (dev)
1. Crie e ative venv:
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

2. Exporte variáveis:
export GEMINI_API_KEY="seu_gemini_key"
export HF_TOKEN="seu_hf_token"

3. Rodar:
fuser -k 8080/tcp || true
python app.py

4. Abra o public URL (gradio.live) ou http://localhost:8080

## Arquitetura
(Colocar diagrama simples e link para imagem)

## Roadmap
- [ ] UI customizada (listening/thinking/speaking)
- [ ] Persistência em Cloud Storage
- [ ] Cloud Run + CI/CD
- [ ] Vídeo live com TURN (próxima fase)

## Contribuição
Veja CONTRIBUTING.md

## License
MIT
