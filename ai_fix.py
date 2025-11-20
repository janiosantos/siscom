import os
import glob
import requests

CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")

def load_logs():
    log_files = glob.glob("logs/**/*.log", recursive=True)
    combined = "\n\n".join(open(f, "r", errors="ignore").read() for f in log_files)
    return combined[:25000]  # limite de segurança

def ask_claude(error_logs):
    payload = {
        "model": "claude-3-5-sonnet",
        "max_tokens": 3000,
        "messages": [
            {
                "role": "system",
                "content": (
                    "Você é Claude Code. Analise os logs de erro abaixo e gere PATCHES "
                    "compatíveis com o repositório atual. "
                    "Retorne APENAS um diff patch aplicável via 'git apply' sem markdown."
                )
            },
            {
                "role": "user",
                "content": f"Logs do CI:\n\n{error_logs}"
            }
        ]
    }

    response = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": CLAUDE_API_KEY,
            "content-type": "application/json",
            "anthropic-version": "2023-06-01"
        },
        json=payload
    )

    data = response.json()
    return data["content"][0]["text"]

def apply_patch(patch):
    with open("ai_patch.diff", "w") as f:
        f.write(patch)

    os.system("git apply ai_patch.diff || true")

def main():
    print("🔍 Carregando logs...")
    logs = load_logs()

    if not logs:
        print("Nenhum log encontrado. Abortando.")
        return

    print("🤖 Enviando logs para Claude...")
    patch = ask_claude(logs)

    print("🪄 Aplicando patch retornado pelo Claude...")
    apply_patch(patch)

    print("✔️ Correções aplicadas com sucesso.")

if __name__ == "__main__":
    main()
