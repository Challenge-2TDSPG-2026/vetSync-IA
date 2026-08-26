# Documentação de Endpoints: Integração IA -> Backend Principal

Este documento detalha os endpoints que precisam ser desenvolvidos no **Backend Principal** para consumir os dados estruturados gerados pela Inteligência Artificial e realizar as devidas manipulações no banco de dados.

---

## 1. Para a funcionalidade de Agendamento (`SchedulingIntent`)

A IA retorna intenções como `RESERVAR`, `CANCELAR`, `CONFIRMAR` ou `CONSULTAR`. Seu backend principal precisará dos seguintes endpoints para manipular o banco:

*   **`GET /api/v1/ia/agendamentos/disponibilidade`**
    *   **Objetivo:** Consultar horários livres de um veterinário em uma data específica.
    *   **Uso:** Quando a IA identificar a intenção `CONSULTAR` (ex: "Quais horários livres amanhã?"), seu sistema baterá nesse endpoint.

*   **`POST /api/v1/ia/agendamentos`**
    *   **Objetivo:** Inserir uma nova consulta no banco.
    *   **Uso:** Recebe o `date_reference`, `time_reference`, `doctor_name` e `patient_name` estruturados pela IA quando a intenção for `RESERVAR`.

*   **`PATCH /api/v1/ia/agendamentos/{id}/status`**
    *   **Objetivo:** Atualizar o estado lógico do evento (`state`) no banco.
    *   **Uso:** Acionado quando a intenção mapeada for `CONFIRMAR` (ex: atualizar para `CONFIRMADO_TUTOR`) ou `CANCELAR` (atualizar para `CANCELADO`).

*   **`PUT /api/v1/ia/agendamentos/{id}/reagendar`**
    *   **Objetivo:** Modificar a data/hora de um registro já existente no banco de dados (Intenção: `REAGENDAR`).

---

## 2. Para o Pós-Atendimento e Prontuário (`ClinicalPostCarePlan`)

A IA extrai o tempo de retorno (`days_until_follow_up`), motivo e necessidade de receita.

*   **`POST /api/v1/ia/atendimentos/{id}/retorno`**
    *   **Objetivo:** Criar um agendamento futuro vinculado ao prontuário.
    *   **Uso:** Você pegará a variável `days_until_follow_up` (ex: 7), somará com a data atual no seu backend, e fará o insert no banco para travar a agenda do médico.

*   **`PATCH /api/v1/ia/atendimentos/{id}`**
    *   **Objetivo:** Atualizar o banco de dados do prontuário indicando pendências.
    *   **Uso:** Atualiza flags no banco utilizando os booleanos `attach_prescription` e `attach_medical_record` que a IA encontrou.

---

## 3. Para a Triagem de Risco (`TriageResult`)

A IA classifica a urgência e extrai sintomas.

*   **`POST /api/v1/ia/triagens`** (ou `POST /api/v1/ia/pre-atendimentos`)
    *   **Objetivo:** Criar um novo registro no banco de dados com a classificação de risco do animal antes mesmo dele chegar à clínica.
    *   **Uso:** Inserir o `urgency_level`, os `identified_symptoms` (array) e atrelar aos IDs do tutor e do pet.

*   **`POST /api/v1/ia/notificacoes/equipe`**
    *   **Objetivo:** Disparar avisos e persistir logs de alerta.
    *   **Uso:** O sistema deve chamar este endpoint se a propriedade `notify_team` for `True` (ex: `EMERGENCIA`).

---

## 4. Para o Check-in Pós-Cirúrgico (`CheckinResult`)

A IA extrai o status da recuperação e *red flags* baseada nos relatos do tutor.

*   **`POST /api/v1/ia/cirurgias/{id}/checkins`**
    *   **Objetivo:** Gravar uma nova entrada na linha do tempo da recuperação do paciente.
    *   **Uso:** Recebe o `recovery_status` (ex: `COMPLICACAO_CRITICA`) e os `red_flags` para salvar no histórico clínico do banco de dados.

---

## 5. Para a Mensageria (Transversal a todas as features)

Todas as saídas da sua IA geram um `message_draft` ou `auto_reply_draft`.

*   **`POST /api/v1/ia/mensagens/enviar`**
    *   **Objetivo:** Registrar a mensagem no banco de dados e enviá-la ao WhatsApp/Email do tutor (via webhook ou provedor).
