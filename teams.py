import base64
import json
import os
import re
import time
from datetime import datetime
import requests
import config

API_BASE_URL = "https://assignments.edu.cloud.microsoft/api/v1.0/edu"


def _is_edu_token(auth_header: str) -> bool:
    """
    Verifica se o token JWT possui a permissão específica de leitura de tarefas do Teams (EduAssignments).
    """
    if not auth_header or not auth_header.lower().startswith("bearer eyj"):
        return False
    try:
        token_clean = auth_header.replace("Bearer ", "").replace("bearer ", "").strip()
        parts = token_clean.split(".")
        if len(parts) >= 2:
            payload_b64 = parts[1] + "=" * ((4 - len(parts[1]) % 4) % 4)
            dados = json.loads(base64.urlsafe_b64decode(payload_b64))
            scp = dados.get("scp", "")
            aud = dados.get("aud", "")
            if "EduAssignments" in scp or aud == "8f348934-64be-4bb2-bc16-c54c96789f43":
                return True
    except Exception:
        pass
    return False


def verificar_validade_token() -> tuple[bool, str]:
    """
    Decodifica o token JWT da Microsoft e verifica a data/hora de expiração e escopos.
    Retorna: (valido: bool, mensagem_formatada: str)
    """
    token = config.TEAMS_AUTH_TOKEN
    if not token or "..." in token:
        return False, "Token não configurado no .env"

    if not _is_edu_token(token):
        return False, "Token expirado ou sem permissão de tarefas"

    token_limpo = token.replace("Bearer ", "").replace("bearer ", "").strip()
    partes = token_limpo.split(".")
    if len(partes) < 2:
        return False, "Formato de token inválido"

    try:
        payload_b64 = partes[1] + "=" * ((4 - len(partes[1]) % 4) % 4)
        dados = json.loads(base64.urlsafe_b64decode(payload_b64))
        exp_timestamp = dados.get("exp")
        if not exp_timestamp:
            return True, "Token sem expiração definida"

        exp_dt = datetime.fromtimestamp(exp_timestamp)
        agora = datetime.now()

        if agora >= exp_dt:
            return False, f"Token EXPIRADO às {exp_dt.strftime('%H:%M:%S')}"

        restante = exp_dt - agora
        minutos_restantes = int(restante.total_seconds() // 60)
        return True, f"Token válido até {exp_dt.strftime('%H:%M:%S')} (~{minutos_restantes} min restantes)"
    except Exception as e:
        return True, f"Não foi possível verificar expiração: {e}"


def salvar_novo_token_no_env(novo_token: str) -> None:
    """Atualiza a variável TEAMS_AUTH_TOKEN no arquivo .env e no ambiente de execução."""
    novo_token = novo_token.strip().strip("'\"")
    if not novo_token.lower().startswith("bearer "):
        novo_token = f"Bearer {novo_token}"

    config.TEAMS_AUTH_TOKEN = novo_token
    os.environ["TEAMS_AUTH_TOKEN"] = novo_token

    env_path = config.ENV_PATH
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            conteudo = f.read()

        if "TEAMS_AUTH_TOKEN=" in conteudo:
            novo_conteudo = re.sub(
                r"TEAMS_AUTH_TOKEN=.*",
                f"TEAMS_AUTH_TOKEN={novo_token}",
                conteudo
            )
        else:
            novo_conteudo = conteudo + f"\nTEAMS_AUTH_TOKEN={novo_token}\n"

        with open(env_path, "w", encoding="utf-8") as f:
            f.write(novo_conteudo)


def renovar_token_automatico() -> str:
    """
    Inicia o navegador de forma nativa em segundo plano, abre o Teams, clica na aba de Tarefas
    e intercepta o token oficial EduAssignments automaticamente.
    """
    from playwright.sync_api import sync_playwright

    user_data_dir = config.BASE_DIR / ".teams_browser_session"
    url_teams = "https://teams.cloud.microsoft/v2/"

    print("\n" + "=" * 60)
    print("   RENOVAÇÃO AUTOMÁTICA DE ACESSO AO TEAMS")
    print("=" * 60)
    print("Conectando ao Teams para capturar novo token de sessão...")

    token_capturado = None

    try:
        with sync_playwright() as p:
            context = p.chromium.launch_persistent_context(
                user_data_dir=str(user_data_dir),
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-gpu",
                ]
            )

            page = context.pages[0] if context.pages else context.new_page()

            def interceptar(request):
                nonlocal token_capturado
                auth = request.headers.get("authorization")
                if auth and _is_edu_token(auth):
                    token_capturado = auth

            page.on("request", interceptar)
            context.on("page", lambda p_nova: p_nova.on("request", interceptar))

            # 1. Abre a página inicial do Teams
            try:
                page.goto(url_teams, timeout=35000)
                page.wait_for_timeout(4000)
            except Exception:
                pass

            # 2. Clica na aba de Tarefas (Assignments) para forçar o carregamento do token
            try:
                btn = page.get_by_text("Assignments", exact=True)
                if btn.count() == 0:
                    btn = page.get_by_text("Trabalhos", exact=True)
                if btn.count() == 0:
                    btn = page.get_by_text("Tarefas", exact=True)
                if btn.count() > 0:
                    btn.first.click(timeout=8000)
            except Exception:
                pass

            # 3. Aguarda o token ser emitido
            for _ in range(15):
                if token_capturado:
                    break
                time.sleep(1)

            context.close()

    except Exception as e:
        print(f"[!] Aviso no processo de captura: {e}")

    if token_capturado and _is_edu_token(token_capturado):
        salvar_novo_token_no_env(token_capturado)
        print("\n✅ Token capturado e salvo no .env de forma 100% automática!\n")
        return token_capturado
    else:
        print("\n[!] Não foi possível capturar o token de tarefas automaticamente.")
        return _renovar_token_fallback()


def _renovar_token_fallback() -> str:
    """Fallback manual caso o usuário prefira colar o token diretamente."""
    print("Cole o valor de 'Authorization' (Bearer eyJ...) abaixo para continuar:")
    try:
        entrada = input("Token: ").strip()
    except (KeyboardInterrupt, EOFError):
        raise RuntimeError("Renovação cancelada.")

    if "eyJ" in entrada:
        salvar_novo_token_no_env(entrada)
        return config.TEAMS_AUTH_TOKEN
    raise RuntimeError("Token inválido.")


def _obter_headers() -> dict:
    """Prepara os cabeçalhos HTTP necessários para as requisições."""
    token = config.TEAMS_AUTH_TOKEN
    if not token or "..." in token:
        raise ValueError(
            "TEAMS_AUTH_TOKEN não configurado no .env! "
            "Por favor, configure o token de autorização do Teams."
        )

    if not token.lower().startswith("bearer "):
        token = f"Bearer {token}"

    return {
        "Authorization": token,
        "Accept": "application/json",
        "Origin": "https://assignments.edu.cloud.microsoft",
        "Ms-Int-Appid": "assignments-ui",
    }


def obter_disciplinas() -> dict[str, str]:
    """
    Busca todas as disciplinas/turmas da conta acadêmica no Teams.
    Retorna um dicionário mapeando: {class_id: nome_da_disciplina}.
    """
    headers = _obter_headers()
    url = f"{API_BASE_URL}/me/classes"

    resposta = requests.get(url, headers=headers, timeout=15)
    if resposta.status_code == 401:
        raise RuntimeError("TOKEN_EXPIRADO")
    elif resposta.status_code != 200:
        raise RuntimeError(
            f"Falha ao buscar disciplinas (Status {resposta.status_code}): {resposta.text}"
        )

    dados = resposta.json().get("value", [])
    mapa_disciplinas = {}
    for item in dados:
        cid = item.get("id")
        nome = item.get("name", "Sem Nome").strip()
        if cid:
            mapa_disciplinas[cid] = nome

    return mapa_disciplinas


def obter_atividades(mapa_disciplinas: dict[str, str]) -> list[dict]:
    """
    Busca todas as tarefas/assignments de todas as disciplinas.
    Cruza cada tarefa com o nome real da disciplina correspondente.
    """
    headers = _obter_headers()
    url = f"{API_BASE_URL}/me/work"

    resposta = requests.get(url, headers=headers, timeout=15)
    if resposta.status_code == 401:
        raise RuntimeError("TOKEN_EXPIRADO")
    elif resposta.status_code != 200:
        raise RuntimeError(
            f"Falha ao buscar atividades (Status {resposta.status_code}): {resposta.text}"
        )

    dados = resposta.json().get("value", [])
    atividades = []

    for item in dados:
        cid = item.get("classId")
        nome_disciplina = mapa_disciplinas.get(cid, "Outros / Geral")
        titulo = item.get("displayName", "Sem título").strip()
        status = item.get("status", "")
        prazo_iso = item.get("dueDateTime")

        prazo_dt = None
        prazo_formatado = None

        if prazo_iso:
            try:
                prazo_dt = datetime.fromisoformat(prazo_iso.replace("Z", "+00:00")).astimezone()
                prazo_formatado = prazo_dt.strftime("%d/%m/%Y %H:%M")
            except Exception:
                prazo_formatado = prazo_iso

        atividades.append({
            "id": item.get("id"),
            "class_id": cid,
            "disciplina": nome_disciplina,
            "titulo": titulo,
            "prazo_iso": prazo_iso,
            "prazo_dt": prazo_dt,
            "prazo_formatado": prazo_formatado,
            "status": status,
            "concluida": item.get("isCompleted", False),
            "permite_atraso": item.get("allowLateSubmissions", True),
        })

    return atividades
