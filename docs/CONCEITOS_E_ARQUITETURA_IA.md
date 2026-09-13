# Arquitetura e Conceitos de Inteligência Artificial — SIA (Sync Inteligência Artificial)
**Disciplina:** Disruptive Architectures: IoT, IoB & Generative IA  
**Projeto:** ClyvoVet (Mobile) / VetSync (Backend) / SIA (Microsserviço de IA)  
**Parceira Corporativa:** Clyvo Vet  
**Semestre:** 2º Semestre — Sprint 3  

---

## 1. Definição do Problema de Negócio na Jornada Contínua do Pet

### 1.1 O Cenário da "Cultura da Emergência"
No mercado veterinário brasileiro, mais de **60% dos atendimentos em planos de saúde pet ocorrem em pronto-socorro/emergência**, onde o custo médio por evento clínico ultrapassa R$ 800,00. Esse padrão gera:
* **Relação transacional e reativa:** O tutor só procura assistência quando o animal já apresenta quadro crítico de dor ou risco de morte;
* **Falta de prevenção periódica:** Longos períodos de inatividade sem revacinações, vermifugações, check-ups odontológicos ou profilaxias;
* **Custo elevado para clínicas e operadoras:** Aumento severo da sinistralidade médica e evasão do tutor após episódios pontuais.

### 1.2 A Solução da SIA (Sync Inteligência Artificial)
A SIA transforma essa relação reativa em um **Ciclo Contínuo de Cuidado (*Health Loop*)**:
1. **Triagem Ativa e Não Prescritiva:** Atua como canal de primeiro contato para interpretar relatos de tutores, classificando o nível de urgência com abordagem clínica conservadora e acionando o pronto-atendimento quando necessário.
2. **Acompanhamento Pós-Atendimento e Pós-Cirúrgico (*Check-in*):** Monitora a recuperação do pet após intervenções cirúrgicas ou consultas, identificando sinais de complicação precocemente (*red flags*).
3. **Agendamento Inteligente com Redução de Atrito:** Facilita a marcação de consultas preventivas e retornos através de linguagem natural (voz ou texto), conectando-se diretamente à disponibilidade médica da clínica.
4. **Produtividade do Médico Veterinário:** Converte comandos falados ou digitados em planos estruturados de alta hospitalar e pós-atendimento sem a necessidade de preenchimento manual burocrático de formulários.

---

## 2. Personalização, Priorização e Apoio à Tomada de Decisão

A IA atua em quatro frentes especializadas de apoio à decisão:

```
                                  ┌────────────────────────────────┐
                                  │   Mensagem / Comando Natural   │
                                  └───────────────┬────────────────┘
                                                  │
                                                  ▼
                                  ┌────────────────────────────────┐
                                  │    SIA Orquestrador (FastAPI)   │
                                  └───────┬───────────────┬────────┘
                                          │               │
                 ┌────────────────────────┼───────────────┼────────────────────────┐
                 ▼                        ▼               ▼                        ▼
        ┌─────────────────┐     ┌─────────────────┐ ┌───────────────┐     ┌─────────────────┐
        │ 1. Triagem de   │     │ 2. Check-in Pós │ │ 3. Agendamento│     │ 4. Pós-Atend.   │
        │    Urgência     │     │    Cirúrgico    │ │    Inteligente│     │    Clínico      │
        └────────┬────────┘     └────────┬────────┘ └───────┬───────┘     └────────┬────────┘
                 │                       │                  │                      │
                 ▼                       ▼                  ▼                      ▼
        [Classificação Risco:   [Classificação:     [Ação / Data / Horário [Plano Estruturado:
         EMERGÊNCIA/URGÊNCIA/   NORMAL/ALERTA/       sem conflitos médicos  retorno, receitas,
         ROTINA/ADMIN]          COMPLICAÇÃO]         via Function Calling]   prontuário, texto]
```

### 2.1 Triagem de Risco (`/api/v1/assistant/triage-inbound`)
* **Critério Conservador:** Em caso de dúvida ou sintomas mistos, a IA sempre opta pela classificação mais grave (`EMERGENCIA`), notificando a equipe da clínica (`notify_team: true`).
* **Sintomas Extraídos:** Isola termos clínicos relevantes a partir do relato leigo do tutor (ex: de *"meu cachorro tá mole e com a gengiva branca"* para `["prostração", "mucosa pálida"]`).

### 2.2 Monitoramento Pós-Cirúrgico (`/api/v1/assistant/parse-checkin-response`)
* **Detecção de *Red Flags*:** Avalia o tempo decorrido da cirurgia (`days_post_surgery`) contra sintomas normais vs sinais de alarme (deiscência de pontos, secreção purulenta, hipotermia, anorexia prolongada).
* **Alerta ao Especialista:** Se `recovery_status == 'COMPLICACAO_CRITICA'`, dispara alerta imediato para o médico responsável.

### 2.3 Agendamento Conversacional com *Function Calling* (`/api/v1/assistant/parse-scheduling`)
* Através de chamadas automáticas de função (`consultar_disponibilidade`), a IA consulta agendas reais e responde propondo horários viáveis sem alucinação.

### 2.4 Pós-Atendimento e Alta (`/api/v1/assistant/parse-intent`)
* Estrutura data de retorno, necessidade de anexos de receitas e prontuários, e produz uma minuta de mensagem personalizada para envio via WhatsApp ou E-mail.

---

## 3. Catálogo e Dicionário de Dados da IA

A tabela abaixo descreve os dados consumidos, transformados e gerados pelo microsserviço de IA:
Em atendimento aos requisitos do Challenge 2026, a IA processa e correlaciona dados estruturados e não-estruturados da jornada de cuidado:

### 3.1 Mapeamento de Entidades do Cuidado Veterinário

* **Perfil do Pet (`PetProfile`):**
  * *Campos:* Nome (`pet_name`), Espécie (`patient_species`: Canina, Felina, etc.), Raça (`breed`), Idade/Data de Nascimento (`age`), Peso (`weight`) e Sexo/Castração (`neutered`).
  * *Uso na IA:* Fornece base de calibração fisiológica para o *System Prompt* do Gemini (ex.: tolerância a sintomas e cálculos temporais diferem entre felinos e caninos).
* **Histórico Clínico e Consultas Anteriores (`ClinicalHistory`):**
  * *Campos:* Diagnósticos prévios, histórico cirúrgico (`past_surgeries`), registros de atendimentos anteriores (`consultation_records`) e comorbidades crônicas (ex.: cardiopatias, insuficiência renal).
  * *Uso na IA:* Permite contextualizar relatos de sintomas e pós-cirúrgicos sem que o tutor precise repetir todo o prontuário.
* **Vacinas e Imunização (`VaccineCard`):**
  * *Campos:* Imunobiológicos aplicados (V8/V10, Antirrábica, FeLV), datas de aplicação e datas de revacinação previstas (`due_vaccine_date`).
  * *Uso na IA:* Identificação ativa de janelas de revacinação para sugestão preditiva de agendamento preventivo no *Health Loop* e descarte de patologias imunopreveníveis.
* **Medicamentos e Prescrições (`Medications`):**
  * *Campos:* Medicamentos em uso contínuo, antibióticos e anti-inflamatórios recentes, dosagem prescrita e reações adversas/alergias (`allergies`).
  * *Uso na IA:* Avaliação na triagem de reações adversas a fármacos e montagem automática do plano estruturado de pós-atendimento (`attach_prescription: true`).
* **Comportamento e Sinais Vitais Relatados (`PetBehavior`):**
  * *Campos:* Padrão alimentar/apetite (anorexia, hiporexia), nível de atividade (letargia, prostração), ingestão hídrica, êmese e alterações comportamentais (gemidos, agressividade induzida por dor).
  * *Uso na IA:* Variáveis decisivas ponderadas pelo modelo durante a classificação de risco (`urgency_level`).

---

### 3.2 Dicionário de Dados de Entrada e Saída do Microsserviço

| Entidade / Campo | Tipo | Origem | Destino | Finalidade na IA |
| :--- | :---: | :---: | :---: | :--- |
| `prompt` / `message` | `str` | Tutor ou Veterinário | SIA / Gemini | Entrada em linguagem natural livre (texto ou transcrição de áudio). |
| `history` | `list[dict]` | Mobile / Sessão | Gemini Context | Histórico de mensagens anteriores para manter coerência multi-turn. |
| `patient_species` | `str` | App / Banco de Dados | Gemini System Prompt | Adaptação do contexto fisiológico (cão, gato, ave, etc.). |
| `days_post_surgery` | `int` | Prontuário / Agenda | Gemini Context | Avaliação da linha temporal esperada de cicatrização pós-operatória. |
| `vaccine_status` | `dict` | Banco de Dados / Core | Gemini Context | Contexto de imunização para sugestão de agendamento preventivo. |
| `current_meds` | `list[str]` | Prontuário / Core | Gemini Context | Fármacos em uso para checagem cruzada de interações e sintomas. |
| `urgency_level` | `str` | Gemini (`TriageResult`) | App / Equipe Médica | Categorização estrita: `EMERGENCIA`, `URGENCIA`, `ROTINA`, `ADMINISTRATIVO`. |
| `identified_symptoms`| `list[str]` | Gemini (`TriageResult`) | Prontuário / Vet | Sintomas clínicos normalizados extraídos do relato livre do tutor. |
| `red_flags` | `list[str]` | Gemini (`CheckinResult`) | Dashboard Vet | Lista de sinais clínicos de complicação detectados no pós-operatório. |
| `action` | `str` | Gemini (`SchedulingIntent`)| Backend Core / Agenda | Ação detectada: `CONSULTAR`, `RESERVAR`, `CANCELAR`, `REAGENDAR`. |
| `days_until_follow_up`| `int` | Gemini (`ClinicalPostCarePlan`)| Agenda / Notificações | Cálculo automático do dia exato para retorno clínico do paciente. |
| `message_draft` | `str` | Gemini | Notificação / Tutor | Rascunho empático e humanizado pronto para envio ao tutor. |

---

## 4. Justificativa Técnica da Abordagem Adotada

A solução adotou **Modelos de Linguagem de Grande Escala (LLM - Google Gemini)** com **Saídas Estruturadas (Pydantic v2)** e **Chamada de Ferramentas (*Function Calling*)**, refutando abordagens tradicionais de NLP baseadas em regras determinísticas ou regex:

1. **Variabilidade Linguística no Meio Veterinário:**
   * Tutores usam linguagem informal, coloquial ou em estado de estresse (*"ele tá vomitando gosma amarela desde ontem"*). Modelos de regras falham miseravelmente ao capturar sinonímias e nuances clínicas.
2. **Eliminação de Alucinações com *Structured Outputs*:**
   * A integração utiliza o recurso nativo `response_schema` com Pydantic v2 do SDK `google-genai`. A LLM é forçada a retornar um JSON estritamente compatível com o modelo de dados, evitando respostas quebradas ou com chaves inexistentes.
3. **Guardrails Rígidos de Segurança Clínica:**
   * As *System Instructions* proíbem expressamente a prescrição de medicamentos, diagnósticos fechados e desvios de assunto (fora do contexto veterinário), garantindo a conformidade ética e jurídica da clínica.
4. **Clean Architecture (*Ports & Adapters*):**
   * O microsserviço isola as regras em UseCases puros (`application/use_cases.py`), desacoplando a camada de transporte (FastAPI) da implementação concreta de IA (`infrastructure/gemini_gateway.py`), facilitando testes com mocks e evolução de modelos.

---

## 5. Diagramas Arquiteturais de Integração

### 5.1 Diagrama de Componentes e Topologia (Visão Macro do Ecossistema)

```mermaid
flowchart TD
    subgraph ClientLayer["Camada de Apresentação (Clientes)"]
        TutorMobile["📱 App Mobile ClyvoVet (React Native / Expo)"]
        VetWeb["💻 Painel da Clínica / Veterinário"]
    end

    subgraph BackendLayer["Camada de Negócio e Orquestração"]
        BackendCore["⚙️ Backend Core VetSync (Spring Boot / REST API)"]
        SIAService["🤖 Microsserviço SIA (FastAPI / Python 3.12)"]
    end

    subgraph IALayer["Serviços de Inteligência Artificial"]
        GeminiLLM["☁️ Google Gemini API (gemini-2.5-flash / Structured Outputs)"]
        FunctionCalling["🛠️ Ferramentas Clínicas (Consultar Agenda / Histórico)"]
    end

    subgraph DataLayer["Camada de Dados e Persistência"]
        OracleDB[("🏛️ Oracle Database 21c (Prontuários, Pets, Consultas)")]
        LocalCache[("🗄️ SQLite / Cache Local de Sessões")]
    end

    TutorMobile -->|"1. Comandos voz/texto, triagem e check-in"| SIAService
    TutorMobile -->|"2. Requisições de negócio padrão"| BackendCore
    VetWeb -->|"3. Gestão de atendimentos e agenda"| BackendCore

    SIAService -->|"4. Autenticação e Sincronização"| BackendCore
    SIAService -->|"5. Prompt enriquecido + Schema Pydantic"| GeminiLLM
    GeminiLLM -->|"6. Function Calling dinâmico"| FunctionCalling
    FunctionCalling -->|"7. Consulta vagas / médicos"| BackendCore
    GeminiLLM -->|"8. JSON Estruturado Validado"| SIAService

    SIAService -->|"9. Gravação de alertas / triagens"| OracleDB
    SIAService -.->|"10. Fallback / Dev"| LocalCache
    BackendCore -->|"11. Transações relacionais ACID"| OracleDB
```

---

### 5.2 Diagrama de Sequência de Integração e Fluxo de Dados

```mermaid
sequenceDiagram
    autonumber
    actor Tutor as Tutor / Veterinário
    participant App as App Mobile (Expo / React Native)
    participant SIA as Microsserviço SIA (FastAPI)
    participant Gemini as Google Gemini (Structured Output)
    participant Core as Backend Core (VetSync)
    participant DB as Oracle Database 21c

    Tutor->>App: Relato de Sintomas / Áudio / Mensagem
    App->>SIA: POST /api/v1/assistant/triage-inbound
    activate SIA
    Note over SIA: Validação do Schema Pydantic
    Note over SIA: Enriquecimento de Contexto (Espécie, Histórico, Vacinas)
    SIA->>Gemini: generate_content(prompt + context, schema=TriageResult)
    activate Gemini
    Gemini-->>SIA: JSON Estruturado (urgency_level, symptoms, draft, notify_team)
    deactivate Gemini
    
    alt urgency_level == 'EMERGENCIA' ou notify_team == true
        SIA->>Core: Notificar Equipe de Emergência da Clínica
        Core->>DB: Grava Alerta Clínico Prioritário
    end

    SIA->>DB: Persiste registro de triagem auditável
    SIA-->>App: Resposta Estruturada com Ações Recomendadas
    deactivate SIA
    App-->>Tutor: Exibe orientações seguras e botão de contato com a clínica
```
