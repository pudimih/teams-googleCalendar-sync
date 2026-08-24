# 🎓 Teams → Google Agenda (Sincronizador Acadêmico)

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Google Calendar API](https://img.shields.io/badge/Google%20Calendar-API-yellow.svg)](https://developers.google.com/calendar)

Um sincronizador automatizado, simples e seguro em Python para integrar suas atividades e tarefas do **Microsoft Teams (Educação)** diretamente ao seu **Google Agenda (Google Calendar)**, com lembretes automáticos e prevenção de duplicações.

---

## ✨ Principais Funcionalidades

- 🔄 **Sincronização 100% Automática:** Captura e renova a sessão do Microsoft Teams de forma autônoma sem exigir cópia manual de tokens ou inspeção de rede (F12).
- 🛡️ **Controle e Privacidade:** O programa pede sua autorização antes de iniciar e permite aprovar cada tarefa nova individualmente ou em lote.
- 🔔 **Lembretes Inteligentes:** Cada atividade criada recebe 3 notificações automáticas no Google Agenda:
  - 📌 **3 dias antes** do prazo final
  - 📌 **1 dia antes** do prazo final
  - 📌 **1 hora antes** do prazo final
- 🚫 **Anti-duplicação:** Identificadores únicos garantem que nenhuma atividade seja inserida repetidamente na sua agenda.
- 🔒 **100% Local:** Suas credenciais, tokens e tarefas nunca saem do seu computador.

---

## 📁 Estrutura do Projeto

```text
teams-google-calendar/
│
├── main.py                   # Ponto de entrada do programa e fluxo de autorizações
├── teams.py                  # Módulo de autenticação, captura de sessão e leitura de tarefas
├── google_calendar.py        # Integração OAuth, criação de eventos e lembretes
├── config.py                 # Configurações globais e resolução de caminhos
├── sincronizar_agenda.bat    # Executável portátil para Windows (1 clique)
├── requirements.txt          # Dependências do projeto
├── .env.example              # Modelo do arquivo de variáveis de ambiente
├── .gitignore                # Arquivos ignorados pelo Git (segredos e cache)
└── LICENSE                   # Licença de código aberto (MIT)
```

---

## 📋 Pré-requisitos

1. **Python 3.10 ou superior** instalado.
2. Conta de estudante no **Microsoft Teams** (instituições de ensino / Teams for Education).
3. Conta no **Google** (onde os eventos serão criados).

---

## ⚙️ Guia de Instalação e Configuração

### 1. Clonar o Repositório
```bash
git clone https://github.com/SEU_USUARIO/teams-google-calendar.git
cd teams-google-calendar
```

### 2. Criar o Ambiente Virtual e Instalar Dependências
```bash
# Criar ambiente virtual
python -m venv .venv

# Ativar ambiente virtual
# No Linux / WSL / macOS:
source .venv/bin/activate
# No Windows (Prompt / PowerShell):
.venv\Scripts\activate

# Instalar pacotes necessários
pip install -r requirements.txt

# Instalar o navegador do Playwright
playwright install chromium
```

> **Nota para usuários de Linux / WSL:** Caso seja a primeira vez utilizando Playwright no Linux, instale as bibliotecas básicas do sistema com:
> ```bash
> sudo apt update && sudo apt install -y libnspr4 libnss3 libasound2t64
> ```

---

### 3. Configurar as Credenciais do Google Calendar

Para permitir que o script adicione eventos à sua agenda pessoal:

1. Acesse o [Google Cloud Console](https://console.cloud.google.com/).
2. Crie um novo projeto (ex: `Sincronizador Teams`).
3. No menu lateral, acesse **APIs e Serviços** → **Biblioteca**, busque por **Google Calendar API** e clique em **Ativar**.
4. Acesse **APIs e Serviços** → **Tela de consentimento OAuth**:
   - Tipo de usuário: **Externo**.
   - Preencha o nome do app e seu e-mail.
   - Em **Usuários de teste**, adicione o seu endereço de e-mail do Google (gmail).
5. Acesse **APIs e Serviços** → **Credenciais**:
   - Clique em **+ Criar Credenciais** → **ID do cliente OAuth**.
   - Tipo de aplicativo: **App para Computador (Desktop App)**.
   - Clique em **Criar** e faça o download do arquivo JSON.
6. Renomeie o arquivo baixado para **`credentials.json`** e coloque-o na raiz da pasta do projeto.

---

### 4. Configurar o Arquivo `.env`

Copie o arquivo de exemplo:
```bash
cp .env.example .env
```
*(Não é necessário preencher o token no `.env`: o script captura a sessão automaticamente no primeiro uso).*

---

## 🚀 Como Executar

### Opção A: Pelo Terminal
```bash
python main.py
```

### Opção B: Pelo Windows (1 Clique)
Basta dar um duplo clique no arquivo **`sincronizar_agenda.bat`**!

---

## 🕹️ Como Funciona o Fluxo de Execução

1. **Permissão de Inicialização:** O programa pergunta se você deseja sincronizar naquele momento (`S/N`).
2. **Autenticação Automática:**
   - Na primeira vez, o navegador abrirá para você fazer login no Teams com sua conta escolar/acadêmica.
   - O login fica salvo localmente no seu computador. Nas próximas execuções, o token é renovado silenciosamente em ~3 segundos!
3. **Revisão de Atividades:**
   - Se houver novas atividades postadas pelo professor, o terminal exibirá a matéria, o título e o prazo, permitindo escolher:
     - `[S]` Sim (adicionar à agenda)
     - `[N]` Não (pular)
     - `[T]` Adicionar Todas de uma vez
     - `[C]` Cancelar

---

## 🛡️ Segurança e Privacidade

- **Zero compartilhamento externo:** O código roda inteiramente no seu computador. Nenhuma informação é enviada a servidores de terceiros.
- **Armazenamento seguro:** As credenciais OAuth do Google (`credentials.json`, `token.json`) e as sessões locais do navegador (`.teams_browser_session/`) estão protegidas no `.gitignore` e nunca são versionadas no repositório.

---

## 📄 Licença

Este projeto é distribuído sob a licença **MIT**. Consulte o arquivo [LICENSE](LICENSE) para mais detalhes.
