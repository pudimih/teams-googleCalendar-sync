import json
import os
import urllib.parse
from datetime import timedelta
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from config import (
    CREDENTIALS_FILE,
    GOOGLE_CALENDAR_ID,
    GOOGLE_SCOPES,
    GOOGLE_TOKEN_FILE,
    SYNCED_FILE,
)


def obter_servico_google():
    """
    Autentica o usuário na Google Calendar API usando OAuth 2.0.
    Reutiliza token salvo em token.json para evitar logins repetidos.
    """
    creds = None

    if os.path.exists(GOOGLE_TOKEN_FILE):
        try:
            creds = Credentials.from_authorized_user_file(str(GOOGLE_TOKEN_FILE), GOOGLE_SCOPES)
        except Exception:
            creds = None

    # Se as credenciais não existirem ou forem inválidas, faz login
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(CREDENTIALS_FILE):
                raise FileNotFoundError(
                    f"Arquivo 'credentials.json' não encontrado na pasta do projeto!\n"
                    f"Caminho esperado: {CREDENTIALS_FILE}\n"
                    f"Consulte o README.md para obter seu credentials.json no Google Cloud Console."
                )

            flow = InstalledAppFlow.from_client_secrets_file(
                str(CREDENTIALS_FILE),
                GOOGLE_SCOPES
            )

            try:
                # Tenta capturar automaticamente via servidor local na porta 8080
                creds = flow.run_local_server(
                    port=8080,
                    bind_addr="0.0.0.0",
                    open_browser=True,
                    success_message="Autenticacao concluida com sucesso! Voce ja pode fechar esta aba e voltar ao terminal."
                )
            except Exception:
                # Fallback manual caso a conexão automática no WSL/Windows seja bloqueada
                auth_url, _ = flow.authorization_url(prompt="consent", access_type="offline")
                print("\n" + "=" * 60)
                print("AUTENTICAÇÃO DO GOOGLE:")
                print(f"1. Acesse o link: {auth_url}")
                print("2. Após autorizar, se a página disser 'não é possível acessar esse site',")
                print("   copie a URL completa da barra de endereços e cole abaixo:")
                print("=" * 60 + "\n")
                entrada = input("Cole a URL ou o código aqui: ").strip()
                if "code=" in entrada:
                    parsed = urllib.parse.urlparse(entrada)
                    params = urllib.parse.parse_qs(parsed.query)
                    code = params.get("code", [entrada])[0]
                else:
                    code = entrada
                flow.fetch_token(code=code)
                creds = flow.credentials

        # Salva o token gerado para as próximas execuções
        with open(GOOGLE_TOKEN_FILE, "w", encoding="utf-8") as token_file:
            token_file.write(creds.to_json())

    return build("calendar", "v3", credentials=creds)


def carregar_atividades_sincronizadas() -> set[str]:
    """Lê o arquivo local que armazena os IDs das atividades já sincronizadas."""
    if not os.path.exists(SYNCED_FILE):
        return set()
    try:
        with open(SYNCED_FILE, "r", encoding="utf-8") as f:
            dados = json.load(f)
            return set(dados.get("synced_ids", []))
    except Exception:
        return set()


def salvar_atividade_sincronizada(atividade_id: str) -> None:
    """Registra o ID de uma atividade sincronizada no arquivo local."""
    sincronizados = carregar_atividades_sincronizadas()
    sincronizados.add(atividade_id)
    with open(SYNCED_FILE, "w", encoding="utf-8") as f:
        json.dump({"synced_ids": list(sincronizados)}, f, indent=2)


def criar_evento_atividade(
    servico,
    atividade: dict,
    ids_ja_sincronizados: set[str],
    calendar_id: str = GOOGLE_CALENDAR_ID
) -> tuple[bool, str]:
    """
    Cria um evento no Google Calendar para uma atividade do Teams.
    Evita duplicações e adiciona lembretes de 3 dias, 1 dia e 1 hora antes.

    Retorna: (sucesso: bool, mensagem: str)
    """
    atividade_id = atividade["id"]
    prazo_dt = atividade.get("prazo_dt")

    # 1. Se a atividade não tiver prazo definido, não cria evento
    if not prazo_dt:
        return False, "Atividade sem prazo de entrega definido."

    # 2. Verificação anti-duplicação local
    if atividade_id in ids_ja_sincronizados:
        return False, "Atividade já sincronizada anteriormente (arquivo local)."

    # 3. Formatação dos horários
    # O evento terminará no horário do prazo e começará 30 minutos antes
    fim_iso = prazo_dt.isoformat()
    inicio_dt = prazo_dt - timedelta(minutes=30)
    inicio_iso = inicio_dt.isoformat()

    titulo_evento = f"📚 {atividade['disciplina']} — {atividade['titulo']}"
    descricao_evento = (
        f"Atividade do Microsoft Teams\n"
        f"Disciplina: {atividade['disciplina']}\n"
        f"Tarefa: {atividade['titulo']}\n"
        f"Prazo final: {atividade['prazo_formatado']}\n"
        f"ID: {atividade_id}"
    )

    corpo_evento = {
        "summary": titulo_evento,
        "description": descricao_evento,
        "start": {
            "dateTime": inicio_iso,
        },
        "end": {
            "dateTime": fim_iso,
        },
        # Lembretes automáticos configurados:
        # - 3 dias antes (4320 minutos)
        # - 1 dia antes (1440 minutos)
        # - 1 hora antes (60 minutos)
        "reminders": {
            "useDefault": False,
            "overrides": [
                {"method": "popup", "minutes": 4320},  # 3 dias antes
                {"method": "popup", "minutes": 1440},  # 1 dia antes
                {"method": "popup", "minutes": 60},    # 1 hora antes
            ],
        },
        # Identificador oculto para evitar duplicação no Google Calendar
        "extendedProperties": {
            "private": {
                "teams_assignment_id": atividade_id,
            }
        },
    }

    try:
        # 4. Verificação extra anti-duplicação direto na API do Google Calendar
        busca = servico.events().list(
            calendarId=calendar_id,
            privateExtendedProperty=f"teams_assignment_id={atividade_id}",
            maxResults=1
        ).execute()

        if busca.get("items"):
            salvar_atividade_sincronizada(atividade_id)
            return False, "Atividade já existe no Google Calendar."

        # 5. Criar o evento no Google Calendar
        evento_criado = servico.events().insert(
            calendarId=calendar_id,
            body=corpo_evento
        ).execute()

        # 6. Registrar a sincronização concluída
        salvar_atividade_sincronizada(atividade_id)
        return True, f"Evento criado com sucesso (ID: {evento_criado.get('id')})"

    except Exception as e:
        return False, f"Erro ao criar evento no Google Calendar: {e}"
