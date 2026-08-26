# Funcionalidades da Inteligência Artificial (SIA - Sync Inteligência Artificial)

A SIA é a assistente virtual especializada em rotinas clínicas veterinárias integrada ao sistema VetSync. Ela atua processando linguagem natural por meio da API do Google Gemini, transformando comandos não estruturados em objetos de domínio (`schemas` ou `models`) rigorosamente tipados para serem processados pela aplicação.

Abaixo estão descritas as duas principais funcionalidades integradas até o momento:

---

## 1. Processamento de Pós-Atendimento Clínico (`/parse-intent`)

Esta funcionalidade foi desenhada para facilitar a vida do médico veterinário ao término de uma consulta. Em vez de preencher formulários com datas, nomes e motivos de retorno, o veterinário pode enviar um comando de voz ou texto corrido. A SIA estrutura essa intenção.

### Como funciona:
O veterinário envia um prompt, como por exemplo:
> *"O Thor operou hoje, a dona Maria precisa trazer ele daqui a 7 dias para tirar os pontos, anexa a receita de antibiótico."*

A IA processa o texto e retorna os dados de forma estruturada:
- **`pet_name`**: Identifica o nome do pet (ex: "Thor").
- **`tutor_name`**: Identifica o nome do tutor (ex: "Maria").
- **`days_until_follow_up`**: Calcula a quantidade de dias para o retorno (ex: `7`).
- **`follow_up_reason`**: Extrai o motivo do retorno (ex: "Tirar os pontos").
- **`attach_prescription`**: Identifica a necessidade de anexos (ex: `true` para a receita).
- **`attach_medical_record`**: Identifica se é necessário o prontuário.
- **`message_draft`**: Cria um rascunho de mensagem amigável para enviar pelo WhatsApp ou E-mail para o tutor, no tom ideal para clínicas veterinárias.

---

## 2. Agendamento Inteligente (`/parse-scheduling`)

Esta funcionalidade foca na orquestração da agenda da clínica veterinária, permitindo interações complexas tanto com o **doutor** quanto com o **tutor**, extraindo ações e referências temporais exatas que, combinadas ao motor de calendário do sistema, garantem reservas sem conflitos.

### Como funciona:
O usuário (médico ou tutor) pode enviar comandos em formato de texto. 
Exemplos:
> *"Quero marcar o retorno do Thor daqui 7 dias no período da tarde."*
> *"Quais horários a Dra. Silva tem livre amanhã?"*
> *"Cancela a minha consulta."*

A IA processa o texto e retorna a intenção de agendamento categorizada:
- **`action`**: A ação principal identificada (`CONSULTAR`, `RESERVAR`, `CONFIRMAR`, `CANCELAR`, `REAGENDAR`, `OPCOES_TUTOR`, `SAUDACAO`, `ASSUNTO_INVALIDO`).
- **`date_reference`**: Expressão da data (ex: "daqui 7 dias", "amanhã"). O sistema usará este campo para fazer o cálculo matemático do dia correto na agenda.
- **`time_reference`**: Expressão do horário (ex: "tarde", "15h").
- **`doctor_name` / `patient_name`**: Identificação do Doutor e do Pet/Tutor.
- **`state`**: O estado lógico do evento, auxiliando o sistema de status do banco de dados (ex: `PENDENTE_DOUTOR`, `AGUARDANDO_TUTOR`, `CONFIRMADO`).
- **`message_draft`**: Texto gerado para interagir e responder adequadamente ao usuário (sugerindo horários ou confirmando a ação).

---

## 3. Triagem e Classificação de Risco no Chat do Tutor (`/triage-inbound`)

Esta funcionalidade atua como a primeira linha de atendimento para mensagens enviadas por tutores através do WhatsApp ou chat da clínica. A SIA **não faz diagnósticos ou prescrições**, mas identifica sinais de risco e classifica a urgência para guiar o fluxo interno de atendimento.

### Como funciona:
O tutor envia uma mensagem informando o estado do animal, como por exemplo:
> *"Meu cachorro foi picado por uma abelha, o focinho dele está muito inchado e ele está com dificuldade pra respirar."*

A IA processa o relato e retorna:
- **`urgency_level`**: Nível de urgência (`EMERGENCIA`, `URGENCIA`, `ROTINA`, `ADMINISTRATIVO`). Há uma instrução rígida para a IA agir de forma conservadora (optar pelo mais grave em caso de dúvida).
- **`identified_symptoms`**: Lista de sintomas efetivamente relatados (ex: `["edema facial", "dificuldade respiratória"]`).
- **`suggested_action`**: Orientação do fluxo da clínica (ex: "Encaminhar imediatamente para atendimento presencial").
- **`auto_reply_draft`**: Resposta segura e objetiva a ser devolvida ao tutor.
- **`notify_team`**: Booleano (`true`/`false`) que sinaliza para o backend se a equipe precisa ser alertada imediatamente.

---

## 4. Monitoramento Ativo de Recuperação Pós-Cirúrgica (`/parse-checkin-response`)

Esta funcionalidade tem como objetivo analisar as respostas de tutores durante o acompanhamento (check-in) pós-operatório. A IA detecta sinais normais de cicatrização ou alertas de complicações para que o médico atue no momento correto.

### Como funciona:
O tutor responde a uma mensagem de acompanhamento:
> *"Ele tomou o remédio, mas o corte da cirurgia tá saindo um líquido amarelo e ele tá meio prostrado."*

A IA estruturará o relato retornando:
- **`recovery_status`**: Estado atualizado (`NORMAL`, `ALERTA_MODERADO`, `COMPLICACAO_CRITICA`).
- **`red_flags`**: Identificadores de risco baseados no relato do tutor (ex: `["secreção na incisão", "prostração"]`).
- **`notify_veterinarian`**: Booleano indicando que um humano precisa atuar no caso.
- **`message_draft`**: Rascunho para dar vazão à interação com o tutor.

---

## Comportamentos Comuns e Limites da IA (Guardrails)

Ambas as integrações compartilham restrições de comportamento configuradas nas "System Instructions":
* **Tratamento de Saudações:** Ao receber um "Bom dia" ou "Olá", a IA responde educadamente se identificando, sem gerar processamento inútil de dados.
* **Prevenção de Alucinação (Assuntos fora do Escopo):** Se questionada sobre clima, esportes, notícias ou qualquer assunto não relacionado a uma clínica veterinária, a SIA educadamente recusa o processamento informando sua função real, sem ser repetitiva.
* **Structured Output Garantido:** O sistema utiliza `response_schema` com Pydantic, garantindo 100% de precisão de que a LLM devolverá as chaves do JSON perfeitamente preenchidas, descartando saídas que possam quebrar a aplicação.
