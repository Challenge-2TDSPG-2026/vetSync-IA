# 🤖 SIA (Sync Inteligência Artificial) — Microsserviço de IA Veterinária

**Projeto:** ClyvoVet (Mobile) / VetSync (Backend Core) / SIA (Inteligência Artificial)  
**Parceira Corporativa:** Clyvo Vet  
**Curso:** Análise e Desenvolvimento de Sistemas — 2º Ano ADS (FIAP 2026)  
**Disciplina:** Disruptive Architectures: IoT, IoB & Generative IA (Sprint 3)  

A **SIA** é a assistente virtual e microsserviço inteligente de rotinas veterinárias integrado ao ecossistema ClyvoVet/VetSync. Construída com **FastAPI**, **Python 3.12** e o modelo **Google Gemini**, ela processa comandos em linguagem natural de tutores e médicos veterinários, transformando relatos desestruturados em objetos de domínio estritamente tipados (*Structured Outputs* via Pydantic v2).
### 👥 Integrantes do Grupo
* Arthu Brito da Silva (RM: 562085)
* Luiz Felipe Flosi dos Santos (RM: 563197)
* Pedro Henrique Brum Lopes (RM: 561780)

### 🎬 Vídeo Pitch de Apresentação (~5 minutos)
* 📺 **Link do Vídeo no YouTube (Modo Não Listado):** `https://youtu.be/lwjRRtU1Tx4`

---

## 📑 Sumário
1. [Problema de Negócio e Valor da Solução](#1-problema-de-negócio-e-valor-da-solução)
2. [Funcionalidades Principais da IA](#2-funcionalidades-principais-da-ia)
3. [Arquitetura Técnica e Guardrails](#3-arquitetura-técnica-e-guardrails)
4. [Requisitos e Configuração do Ambiente](#4-requisitos-e-configuração-do-ambiente)
5. [Como Executar a Aplicação](#5-como-executar-a-aplicação)
6. [Execução dos Testes Automatizados](#6-execução-dos-testes-automatizados)
7. [Documentação da API (Swagger) e Exemplos cURL](#7-documentação-da-api-swagger-e-exemplos-curl)
8. [Resultados Parciais da Sprint 3](#8-resultados-parciais-da-sprint-3)

---

## 1. Problema de Negócio e Valor da Solução

O setor veterinário enfrenta a chamada **"cultura da emergência"**: segundo dados da Clyvo Vet, **60% das utilizações dos planos de saúde ocorrem no pronto-socorro** (com custo médio superior a R$ 800,00 por ocorrência). O tutor médio só procura auxílio quando o pet já está em sofrimento agudo.

A SIA atua diretamente na quebra dessa inércia por meio de um **Ciclo Contínuo de Cuidado (*Health Loop*)**:
- **Atendimento conversacional responsável:** Acolhe o tutor, não faz diagnóstico ou classificação clínica e direciona dúvidas de saúde para avaliação presencial;
- **Prevenção e acompanhamento:** Valoriza relatos positivos e oferece check-ups preventivos para dar tranquilidade ao tutor;
- **Agendamento por linguagem natural:** coleta as escolhas necessárias do tutor e cria o evento no backend Java autenticado;
- **Produtividade clínica:** Converte notas de voz e comandos do veterinário em planos estruturados de pós-atendimento e altas hospitalares.

> 📖 Para aprofundamento técnico, consulte o documento: [Conceitos e Arquitetura de IA](docs/CONCEITOS_E_ARQUITETURA_IA.md).

---

## 2. Funcionalidades Principais da IA

### 2.1 Pós-Atendimento Clínico Estruturado (`/api/v1/assistant/parse-intent`)
Permite ao médico ditar ou digitar orientações pós-consulta. A IA extrai dias para retorno, motivos, necessidade de anexos e gera o rascunho da mensagem ao tutor.

### 2.2 Agendamento Inteligente (`/api/v1/ia/orquestrador/processar`)
Ao iniciar um agendamento, a SIA consulta no backend Java os pets do tutor, tipos de evento e veterinários. Ela pede a escolha de **pet, tipo de atendimento, veterinário, data e horário**; a data é sempre confirmada de forma absoluta (por exemplo, `dia 20` em 18/09/2026 vira `20/09/2026`). Só depois de todos os campos serem escolhidos ela encaminha o mesmo Bearer do tutor para `POST /eventos` e confirma a consulta se o Java retornar sucesso. Nome e telefone não são pedidos porque não pertencem a esse contrato.

### 2.3 Conversa com o Tutor (`/api/v1/ia/orquestrador/processar`)
Mantém o histórico da conversa e o contexto do pet para responder de maneira natural. Não expõe categorias, não realiza triagem nem diagnóstico; relatos de saúde são orientados para avaliação presencial na clínica.

### 2.4 Monitoramento Ativo Pós-Cirúrgico (`/api/v1/assistant/parse-checkin-response`)
Interpreta relatos de tutores sobre a evolução de cirurgias, avaliando cicatrização e acionando o veterinário em caso de sinais críticos (*red flags*).

### 2.5 Chat In-App (`/api/v1/in-app/chat/tutor`)
Responde ao tutor com o histórico da conversa, sem rótulos técnicos ou classificação de intenção.

---

## 3. Arquitetura Técnica e Guardrails

- **Padrão Arquitetural:** Clean Architecture (*Ports & Adapters*) separando Domínio (`domain/`), Casos de Uso (`application/`), Gateways externos (`infrastructure/`) e Rotas (`presentation/`).
- **SDK Oficial:** `google-genai` com o modelo `gemini-3.5-flash-lite`.
- **Structured Outputs:** Validação 100% garantida por esquemas `Pydantic v2` via parâmetro `response_schema`.
- **Guardrails de Segurança Clínica:**
  - **Sem diagnóstico ou triagem:** A SIA não avalia gravidade, não prescreve e orienta avaliação presencial quando o tutor relata ou tem dúvida sobre a saúde do pet.
  - **Conversa natural:** Saudações e assuntos fora da clínica recebem respostas breves e educadas, sem mensagens robóticas de classificação.

---

## 4. Requisitos e Configuração do Ambiente

### Pré-requisitos
- **Python 3.12+** instalado
- Chave de API do **Google Gemini** ([Google AI Studio](https://aistudio.google.com/))

### Passo a Passo de Instalação

1. **Acesse a pasta do projeto:**
   ```bash
   cd /home/felipeflosi/Documentos/FIAP/Challenge/IA
   ```

2. **Crie e ative o ambiente virtual:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Instale as dependências:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure as variáveis de ambiente:**
   Copie o arquivo de exemplo e insira sua chave da API:
   ```bash
   cp .env.example .env
   ```
   Edite o arquivo `.env`:
   ```ini
   GEMINI_API_KEY=sua_chave_do_gemini_aqui
   ORACLE_DB_URL=oracle+oracledb://RMXXXXXX:senha@oracle.fiap.com.br:1521/?service_name=ORCL
   AUTH_JWT_SECRET=sua_chave_jwt_secreta_aqui
   JAVA_API_BASE_URL=https://sua-api-java.example.com
   ```

   `JAVA_API_BASE_URL` é obrigatória para o agendamento conversacional. Em produção, `AUTH_JWT_SECRET` deve coincidir exatamente com o segredo que assina o JWT no Java, para que o Bearer possa ser validado aqui e repassado ao Java.

---

## 5. Como Executar a Aplicação

### Execução Local (Desenvolvimento)
Com o ambiente virtual ativado:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```
A API estará acessível em: `http://localhost:8000`

### Execução via Docker
Para rodar a aplicação em container:
```bash
# Construir a imagem Docker
docker build -t clyvovet-ia:latest .

# Executar o container na porta 8000
docker run -d -p 8000:8000 --env-file .env --name clyvovet-ia-container clyvovet-ia:latest
```

---

## 6. Execução dos Testes Automatizados

A suíte de testes unitários e de integração utiliza **pytest** com mocks das portas de integração para execução rápida e determinística (sem consumo da API de produção):

```bash
# Executar todos os testes
pytest

# Executar com detalhes de cada teste (modo verboso)
pytest -v
```

Para rodar o script de teste ao vivo contra a API do Google Gemini:
```bash
python tests/run_test.py
```

---

## 7. Documentação da API (Swagger) e Exemplos cURL

A documentação interativa OpenAPI/Swagger está disponível em:
- **Swagger UI:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Redoc:** [http://localhost:8000/redoc](http://localhost:8000/redoc)

### Exemplos de Chamada via cURL

#### 1. Verificação de Saúde (Health Check)
```bash
curl -X GET http://localhost:8000/health
```
**Resposta esperada:**
```json
{"status": "ok"}
```

#### 2. Pós-Atendimento Veterinário (`/api/v1/assistant/parse-intent`)
```bash
curl -X POST http://localhost:8000/api/v1/assistant/parse-intent \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "O Rex operou hoje, o tutor João precisa trazer ele daqui a 7 dias para retirar os pontos. Anexa a receita de anti-inflamatório e avisa que correu tudo bem."
  }'
```
**Resposta estruturada da IA:**
```json
{
  "pet_name": "Rex",
  "tutor_name": "João",
  "days_until_follow_up": 7,
  "follow_up_reason": "Retirada de pontos",
  "attach_prescription": true,
  "attach_medical_record": false,
  "message_draft": "Olá, João! Tudo bem? O Rex já está se recuperando da cirurgia e correu tudo muito bem! Segue em anexo a receita do anti-inflamatório. Lembre-se de trazê-lo daqui a 7 dias para a retirada dos pontos. Qualquer dúvida, conte conosco!"
}
```

#### 3. Conversa de Saúde no Chat do Tutor (`/api/v1/ia/orquestrador/processar`)
```bash
curl -X POST http://localhost:8000/api/v1/ia/orquestrador/processar \
  -H "Content-Type: application/json" \
  -d '{
    "message": "A Morgana caiu da escada. Devo levá-la à clínica?",
    "contexto": {"pet_ativo": {"nome": "Morgana"}}
  }'
```
**Resposta conversacional da IA:**
```json
{
  "mensagem": "Sinto muito que isso tenha acontecido com a Morgana. Não consigo avaliá-la ou diagnosticar pelo chat; se você está em dúvida sobre levá-la, o mais seguro é trazê-la para uma avaliação presencial na clínica."
}
```

#### 4. Agendamento Inteligente (`/api/v1/assistant/parse-scheduling`)
```bash
curl -X POST http://localhost:8000/api/v1/assistant/parse-scheduling \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Gostaria de agendar uma consulta para amanhã à tarde com o Dr. Carlos para a gatinha Luna"
  }'
```
**Resposta da IA:**
```json
{
  "action": "RESERVAR",
  "date_reference": "amanhã",
  "time_reference": "tarde",
  "doctor_name": "Dr. Carlos",
  "patient_name": "Luna",
  "state": "PENDENTE_DOUTOR",
  "message_draft": "Solicitação de agendamento recebida para amanhã no período da tarde com o Dr. Carlos para a Luna. Estamos confirmando a disponibilidade."
}
```

---

## 8. Resultados Parciais da Sprint 3

Em conformidade com os critérios de avaliação da Sprint 3 (Disruptive Architectures), os resultados parciais obtidos demonstram a robustez e estabilidade técnica da solução:

### 8.1 Validação e Testes Automatizados
* **Suíte de Testes (pytest):** 11 testes unitários e de integração cobrindo 100% dos Casos de Uso (`application/use_cases.py`) e Controladores REST (`presentation/assistant_routers.py`).
* **Taxa de Sucesso:** 100% dos testes aprovados (`11 passed in ~1.5s`).
* **Isolamento de Ambiente:** Utilização de mocks nas portas de gateway (`IAssistantGateway`), garantindo testes rápidos, determinísticos e sem custos de consumo de API em esteiras de integração contínua (CI/CD).

### 8.2 Acurácia de Estruturação (*Zero Hallucination* via Pydantic v2)
* **Tipagem Estrita (*Structured Outputs*):** O uso do parâmetro nativo `response_schema` com Pydantic v2 forçou o modelo Google Gemini a retornar payloads JSON estritamente aderentes aos contratos de dados. Em todos os cenários de teste (incluindo relatos informais e ambíguos), nenhuma quebra de chave, omissão de tipo ou retorno de markdown desestruturado foi detectado.
* **Classificação Conservadora de Urgência:** Nos testes com sintomas graves (ex.: intoxicação, prostração extrema, dispneia), a IA classificou a urgência como `EMERGENCIA` e ativou a flag `notify_team: true` em 100% das amostras.

### 8.3 Performance e Guardrails Clínicos
* **Tempo Médio de Processamento:** Respostas de intenção estruturada geradas em menos de 1.8 segundos utilizando o modelo do Google Gemini.
* **Guardrails Ativos:** Saudações simples foram respondidas de forma concisa e amigável sem acionar chamadas pesadas, e perguntas fora de contexto veterinário (clima, política, esportes) foram educadamente recusadas sem alucinações.
