# 🎬 Roteiro Oficial para Gravação do Vídeo Pitch de IA (5 Minutos)

**Disciplina:** Disruptive Architectures: IoT, IoB & Generative IA  
**Projeto:** SIA (Sync Inteligência Artificial) / ClyvoVet  
**Plataforma de Envio:** YouTube (Vídeo em modo Não Listado)  
**Tempo Máximo:** 05:00 minutos  

---

## ⏱️ Linha do Tempo e Minutagem do Pitch

```
00:00 ──► [1. Problema de Negócio & ClyvoVet] (1 min)
01:00 ──► [2. Arquitetura da Solução & Gemini] (1 min 15s)
02:15 ──► [3. Demonstração Prática da SIA] (1 min 30s)
03:45 ──► [4. Guardrails e Segurança Clínica] (45s)
04:30 ──► [5. Impacto de Negócio & Conclusão] (30s)
05:00 ──► Encerramento
```

---

## 📝 Script de Fala e Telas a Exibir

### 1. Introdução e Problema de Negócio (00:00 - 01:00)
* **O que mostrar na tela:** Slide inicial com logotipo da FIAP, ClyvoVet, integrantes da equipe (Arthur, Felipe, Pedro) e a interface do aplicativo mobile ClyvoVet.
* **O que falar:**
  > *"Olá, somos a equipe do projeto ClyvoVet e hoje vamos apresentar a SIA — nossa assistente e microsserviço de inteligência artificial veterinária desenvolvido para a Clyvo Vet.*  
  > *Atualmente, o mercado veterinário sofre com a 'cultura da emergência': mais de 60% dos atendimentos em planos pet acontecem no pronto-socorro, custando mais de R$ 800 por atendimento. O tutor só procura ajuda quando o pet já está em sofrimento agudo, gerando um relacionamento transacional e caro.*  
  > *A SIA resolve esse problema transformando essa postura reativa em um ciclo contínuo de cuidado — o nosso Health Loop —, com triagem inteligente de urgência, monitoramento pós-cirúrgico e facilitação de agendamento por linguagem natural."*

---

### 2. Arquitetura Técnica e Escolha do Google Gemini (01:00 - 02:15)
* **O que mostrar na tela:** Diagrama arquitetural (Mermaid de `docs/CONCEITOS_E_ARQUITETURA_IA.md`) e código-fonte no VS Code destacando a Clean Architecture (`application/`, `domain/`, `infrastructure/`, `presentation/`).
* **O que falar:**
  > *"Tecnicamente, construímos a SIA como um microsserviço de alta performance utilizando Python 3.12 e FastAPI, estruturado no padrão Clean Architecture com Ports & Adapters.*  
  > *Optamos pelo modelo Google Gemini integrado via SDK oficial `google-genai`.*  
  > *Por que essa abordagem em vez de NLP tradicional ou regras fixas? Porque tutores usam linguagem altamente coloquial e variada. Para garantir que a LLM nunca quebre a aplicação com respostas imprevistas, utilizamos o recurso nativo de Structured Outputs com esquemas rigorosos do Pydantic v2. A saída da IA é 100% tipada, validada e pronta para o banco de dados."*

---

### 3. Demonstração Prática dos Recursos Implementados (02:15 - 03:45)
* **O que mostrar na tela:** Swagger UI (`http://localhost:8000/docs`) ou execução no terminal com `tests/run_test.py` e tela do aplicativo mobile interagindo com o chat da SIA.
* **O que falar:**
  > *"Vamos ver a SIA funcionando na prática em três frentes principais:*  
  > *Primeiro, a Triagem de Urgência (`/triage-inbound`): quando um tutor relata sintomas como picada de inseto ou salivação excessiva, a IA extrai os sintomas clínicos e classifica a gravidade de forma conservadora em EMERGÊNCIA, alertando a equipe de plantão.*  
  > *Segundo, o Acompanhamento Pós-Cirúrgico (`/parse-checkin-response`): o tutor responde como o pet está após a operação. A IA avalia o tempo de cirurgia e detecta 'red flags', como deiscência de pontos ou febre, sinalizando se um médico precisa intervir.*  
  > *Terceiro, o Pós-Atendimento e Agendamento: ao término da consulta, o veterinário apenas dita ou digita comandos de voz, e a IA extrai os dias para retorno, gera rascunho de mensagem para o tutor e agenda a consulta sem conflitos através de Function Calling."*

---

### 4. Guardrails e Ética Clínica (03:45 - 04:30)
* **O que mostrar na tela:** Trechos de `prompts.py` mostrando as `System Instructions` e restrições de segurança.
* **O que falar:**
  > *"Um diferencial indispensável da nossa solução são os Guardrails de Segurança Clínica:*  
  > *1. A SIA nunca prescreve medicamentos e não fornece diagnósticos fechados; ela orienta e direciona para atendimento humano seguro.*  
  > *2. Prevenção de alucinação: saudações são tratadas de forma concisa e perguntas fora do domínio veterinário — como esportes, notícias ou clima — são educadamente recusadas.*  
  > *3. Toda a suíte de testes unitários roda com pytest simulando falhas e garantindo integridade de 100% dos endpoints."*

---

### 5. Impacto de Negócio e Encerramento (04:30 - 05:00)
* **O que mostrar na tela:** Slide final com os benefícios para a Clyvo Vet, métricas esperadas e repositório GitHub.
* **O que falar:**
  > *"Com a SIA integrada ao ClyvoVet, aumentamos a retenção e o Lifetime Value do tutor, reduzimos custos de sinistralidade de emergência para as clínicas e operadoras, e garantimos que o animal receba cuidados preventivos constantes.*  
  > *Todo o código-fonte, testes e documentação estão disponíveis no repositório do GitHub Classroom.*  
  > *Muito obrigado!"*
