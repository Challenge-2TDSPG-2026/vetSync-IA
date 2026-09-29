# Documentação de Endpoints: API Assistente Veterinário (vetSync-IA)

Este documento detalha os endpoints disponíveis na aplicação atual, desenvolvida em **FastAPI**. A API utiliza Inteligência Artificial (Google GenAI) para conversar com tutores, estruturar planos de pós-atendimento, acompanhar check-ins e apoiar agendamentos.

Atualmente, o projeto está estruturado em duas categorias principais de endpoints:
1. **Módulo IA + Oracle:** Novas rotas que, além de interpretar a intenção com a IA, já preparam a lógica de persistência e manipulação no banco de dados Oracle.
2. **Módulo Assistant (Apenas processamento de IA):** Rotas originais que recebem o texto e retornam a estrutura JSON gerada pela IA, sem manipulação de banco de dados.

---

## 1. Módulo IA + Oracle (Integração com Banco de Dados)

Estas rotas cuidam de receber os dados do front-end/tutor, interpretá-los usando a Inteligência Artificial e tomar a decisão apropriada no banco de dados (inserir, atualizar, cancelar).

### Agendamento por blocos
* **`POST /api/v1/ia/orquestrador/processar`**
  * **Objetivo:** inicia uma consulta de clínico geral. Com data compreensível,
    devolve `mensagem` e um bloco `SELECIONAR_HORARIO` baseado em
    `GET /agenda/slots` do Java.
  * **Payload:** `{"message": "Quero marcar uma consulta amanhã"}`
* **`POST /api/v1/ia/orquestrador/agendamentos/sessoes/{sessaoId}/selecoes`**
  * **Objetivo:** avança uma opção previamente devolvida pela SIA sem chamar o
    modelo. O corpo é `{"opcaoId": "uuid"}`; as escolhas possíveis são data,
    horário, pet e confirmação.
* **`GET /agenda/slots?data=YYYY-MM-DD&modalidade=CLINICO_GERAL`** *(Java)*
  * **Objetivo:** lista slots livres do tutor autenticado. Não cria reserva.

### Pós-Atendimento e Prontuário (`ClinicalPostCarePlan`)
*   **`POST /api/v1/ia/atendimentos/processar`**
    *   **Objetivo:** Recebe instruções médicas do veterinário (ex: áudio transcrito ou texto corrido), a IA estrutura o prontuário e salva as pendências ou agenda o retorno no Oracle.
    *   **Exemplo de Payload:** `{"prompt": "Animal bem, pedir para voltar daqui a 7 dias e prescrever dipirona"}`

### Conversa com o Tutor
*   **`POST /api/v1/ia/orquestrador/processar`**
    *   **Objetivo:** Responde de forma natural, usando o histórico e o pet ativo. Quando a mensagem inicia agendamento, devolve blocos estruturados; não classifica risco ou urgência e não faz diagnóstico.
    *   **Exemplo de Payload:** `{"message": "A Morgana caiu da escada. Devo levá-la?", "contexto": {"pet_ativo": {"nome": "Morgana"}}}`

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
*   **`POST /parse-checkin-response`**
    *   Avalia a recuperação de um paciente recém-operado. Retorna um objeto do tipo `CheckinResult`.

---

*Nota de Desenvolvimento: As rotas do "Módulo IA + Oracle" já possuem acesso à sessão do banco de dados (`db: Session = Depends(get_db)`) e contêm comentários `TODO` indicando exatamente onde as entidades do SQLAlchemy devem ser persistidas, de acordo com as regras de negócio do banco de dados final.*
