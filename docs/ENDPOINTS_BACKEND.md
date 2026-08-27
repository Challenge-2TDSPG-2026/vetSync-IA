# Documentação de Endpoints: API Assistente Veterinário (vetSync-IA)

Este documento detalha os endpoints disponíveis na aplicação atual, desenvolvida em **FastAPI**. A API utiliza Inteligência Artificial (Google GenAI) para interpretar comandos em linguagem natural e estruturar planos de pós-atendimento, triagem, check-ins e agendamentos.

Atualmente, o projeto está estruturado em duas categorias principais de endpoints:
1. **Módulo IA + Oracle:** Novas rotas que, além de interpretar a intenção com a IA, já preparam a lógica de persistência e manipulação no banco de dados Oracle.
2. **Módulo Assistant (Apenas processamento de IA):** Rotas originais que recebem o texto e retornam a estrutura JSON gerada pela IA, sem manipulação de banco de dados.

---

## 1. Módulo IA + Oracle (Integração com Banco de Dados)

Estas rotas cuidam de receber os dados do front-end/tutor, interpretá-los usando a Inteligência Artificial e tomar a decisão apropriada no banco de dados (inserir, atualizar, cancelar).

### Agendamentos (`SchedulingIntent`)
*   **`POST /api/v1/ia/agendamentos/processar`**
    *   **Objetivo:** Recebe uma mensagem em texto livre do tutor, passa pela IA para estruturar, e toma a ação no banco de dados Oracle baseada na intenção (`RESERVAR`, `CANCELAR`, `CONFIRMAR`, `CONSULTAR`).
    *   **Exemplo de Payload:** `{"prompt": "Quero marcar consulta amanhã as 14h"}`

### Pós-Atendimento e Prontuário (`ClinicalPostCarePlan`)
*   **`POST /api/v1/ia/atendimentos/processar`**
    *   **Objetivo:** Recebe instruções médicas do veterinário (ex: áudio transcrito ou texto corrido), a IA estrutura o prontuário e salva as pendências ou agenda o retorno no Oracle.
    *   **Exemplo de Payload:** `{"prompt": "Animal bem, pedir para voltar daqui a 7 dias e prescrever dipirona"}`

### Triagem de Risco (`TriageResult`)
*   **`POST /api/v1/ia/triagens/processar`**
    *   **Objetivo:** Recebe os sintomas descritos pelo tutor antes de chegar na clínica. A IA classifica o risco (ex: `EMERGENCIA`, `NORMAL`), salva a triagem no Oracle e sinaliza alertas para a equipe se necessário.
    *   **Exemplo de Payload:** `{"message": "Meu cachorro foi atropelado e está vomitando", "pet_id": "123", "patient_species": "CACHORRO"}`

### Check-in Pós-Cirúrgico (`CheckinResult`)
*   **`POST /api/v1/ia/checkins/processar`**
    *   **Objetivo:** Recebe relatos do tutor sobre a recuperação em casa. A IA extrai o status e eventuais complicações (*red flags*), gravando na linha do tempo do paciente (histórico da cirurgia) no Oracle.
    *   **Exemplo de Payload:** `{"message": "A ferida está com pus e quente", "surgery_id": "456", "days_post_surgery": 2}`

---

## 2. Módulo Assistant (Somente IA - Sem Banco de Dados)

Rotas de base originais da aplicação que apenas utilizam o *Gateway* de IA (`GeminiGateway`) para interpretar intenções em texto livre e retornar a tipagem Pydantic (JSON) correspondente.

*   **`POST /api/v1/assistant/parse-intent`**
    *   Estrutura planos clínicos de pós-atendimento. Retorna um objeto do tipo `ClinicalPostCarePlan`.
*   **`POST /api/v1/assistant/parse-scheduling`**
    *   Interpreta intenções de agenda do tutor. Retorna um objeto do tipo `SchedulingIntent`.
*   **`POST /triage-inbound`**
    *   Classifica o nível de risco a partir dos sintomas informados. Retorna um objeto do tipo `TriageResult`.
*   **`POST /parse-checkin-response`**
    *   Avalia a recuperação de um paciente recém-operado. Retorna um objeto do tipo `CheckinResult`.

---

*Nota de Desenvolvimento: As rotas do "Módulo IA + Oracle" já possuem acesso à sessão do banco de dados (`db: Session = Depends(get_db)`) e contêm comentários `TODO` indicando exatamente onde as entidades do SQLAlchemy devem ser persistidas, de acordo com as regras de negócio do banco de dados final.*
