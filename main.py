import os
import sys
from config import CREDENTIALS_FILE, ENV_PATH, TEAMS_AUTH_TOKEN
from teams import (
    verificar_validade_token,
    renovar_token_automatico,
    obter_disciplinas,
    obter_atividades,
)
from google_calendar import (
    obter_servico_google,
    carregar_atividades_sincronizadas,
    criar_evento_atividade,
)


def perguntar_sim_ou_nao(pergunta: str, padrao_sim: bool = True) -> bool:
    """Solicita confirmação simples do usuário."""
    sufixo = " [S/n]: " if padrao_sim else " [s/N]: "
    try:
        resposta = input(pergunta + sufixo).strip().lower()
    except (KeyboardInterrupt, EOFError):
        print("\nOperação cancelada.")
        sys.exit(0)

    if not resposta:
        return padrao_sim
    return resposta in ["s", "sim", "y", "yes"]


def main():
    print("=" * 60)
    print("   Teams -> Google Agenda (Sincronizador Acadêmico)")
    print("=" * 60)

    # 1. PRIMEIRA CAMADA DE AUTORIZAÇÃO: Iniciar ou não a sincronização
    print()
    if not perguntar_sim_ou_nao("Deseja iniciar a sincronização com o Microsoft Teams agora?"):
        print("\nSincronização cancelada por você. Nenhum processo foi executado.\n")
        return

    # 2. Verificar configuração do .env e validade do token
    if not ENV_PATH.exists() or not TEAMS_AUTH_TOKEN or "..." in TEAMS_AUTH_TOKEN:
        print("\n[!] Token do Teams não configurado no .env.")
        print("Iniciando captura automática pelo navegador...")
        renovar_token_automatico()

    valido, msg_token = verificar_validade_token()
    print(f"\n[Token do Teams]: {msg_token}")

    if not valido:
        print("\n[!] O seu token do Teams expirou.")
        print("Iniciando renovação automática pelo navegador do Windows...")
        try:
            renovar_token_automatico()
        except Exception as e:
            print(f"\n[ERRO] {e}")
            sys.exit(1)

    # 3. Buscar turmas e disciplinas no Teams
    print("\nBuscando disciplinas no Microsoft Teams...")
    try:
        mapa_disciplinas = obter_disciplinas()
    except Exception as e:
        if "TOKEN_EXPIRADO" in str(e):
            print("\n[!] O token expirou durante a requisição. Renovando automaticamente...")
            renovar_token_automatico()
            mapa_disciplinas = obter_disciplinas()
        else:
            print(f"\n[ERRO] Falha ao buscar disciplinas: {e}")
            sys.exit(1)

    if not mapa_disciplinas:
        print("\nNenhuma disciplina encontrada na sua conta.")
        return

    print("\nDisciplinas encontradas:\n")
    for nome in mapa_disciplinas.values():
        print(f"- {nome}")

    # 4. Buscar tarefas / assignments no Teams
    print("\n" + "-" * 40)
    print("Buscando tarefas das disciplinas...")
    try:
        atividades = obter_atividades(mapa_disciplinas)
    except Exception as e:
        print(f"\n[ERRO] Falha ao buscar tarefas: {e}")
        sys.exit(1)

    atividades_pendentes = [a for a in atividades if not a["concluida"] and a["prazo_dt"]]
    print(f"\nTotal: {len(mapa_disciplinas)} disciplina(s) e {len(atividades_pendentes)} tarefa(s) pendente(s) com prazo.")
    print("=" * 60)

    # 5. Conectar com o Google Calendar
    if not os.path.exists(CREDENTIALS_FILE):
        print("\n[!] Arquivo 'credentials.json' do Google não encontrado.")
        print(f"    Caminho esperado: {CREDENTIALS_FILE}")
        return

    try:
        servico_google = obter_servico_google()
    except Exception as e:
        print(f"[ERRO] Falha ao conectar no Google Calendar: {e}")
        return

    ids_sincronizados = carregar_atividades_sincronizadas()
    novas_atividades = [a for a in atividades_pendentes if a["id"] not in ids_sincronizados]

    if not novas_atividades:
        print("\n✅ Todas as atividades pendentes já estão sincronizadas no seu Google Agenda!")
        print("   Nenhuma nova atividade precisa ser adicionada.")
        print("=" * 60)
        return

    # 6. SEGUNDA CAMADA DE AUTORIZAÇÃO: Aprovação granular de cada atividade nova
    print(f"\n📢 Foram encontradas {len(novas_atividades)} NOVA(S) atividade(s) para sincronizar:")
    print("=" * 60)

    aprovar_todas = False
    novos_eventos = 0
    ignoradas = 0

    for idx, ativ in enumerate(novas_atividades, 1):
        print(f"\n[ Atividade {idx}/{len(novas_atividades)} ]")
        print(f"📚 Disciplina: {ativ['disciplina']}")
        print(f"📝 Tarefa:     {ativ['titulo']}")
        print(f"⏰ Prazo:      {ativ['prazo_formatado']}")

        adicionar = False

        if aprovar_todas:
            adicionar = True
        else:
            print("\nOpções: [S] Sim (adicionar com lembretes) | [N] Não (pular) | [T] Adicionar Todas | [C] Cancelar")
            try:
                escolha = input("Sua escolha: ").strip().lower()
            except (KeyboardInterrupt, EOFError):
                print("\nOperação cancelada.")
                break

            if escolha in ["t", "todas", "all"]:
                aprovar_todas = True
                adicionar = True
            elif escolha in ["s", "sim", "y", "yes", ""]:
                adicionar = True
            elif escolha in ["c", "cancelar", "cancel"]:
                print("\nSincronização interrompida por você.")
                break
            else:
                adicionar = False

        if adicionar:
            criou, mensagem = criar_evento_atividade(servico_google, ativ, ids_sincronizados)
            if criou:
                novos_eventos += 1
                print(f"  --> ✅ Evento criado no Google Agenda com lembretes!")
            else:
                print(f"  --> ⚠️ {mensagem}")
        else:
            ignoradas += 1
            print("  --> ⏭️ Tarefa pulada.")

    print("\n" + "=" * 60)
    print("Sincronização finalizada:")
    print(f"- {novos_eventos} novo(s) evento(s) adicionado(s) à sua agenda.")
    if ignoradas > 0:
        print(f"- {ignoradas} atividade(s) ignorada(s)/puladas.")
    print("=" * 60)


if __name__ == "__main__":
    main()
