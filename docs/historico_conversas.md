# Suporte a Histórico de Conversas (Contexto Contínuo)

A IA foi atualizada para entender a **continuidade de mensagens**, analisando conversas passadas para melhorar a precisão nas respostas de **Triagem (`/triage-inbound`)** e **Check-in (`/parse-checkin-response`)**.

Como a IA roda no modelo *stateless* (por requisição), o gerenciamento do estado da conversa deve ser feito pelo backend (o banco de dados onde as interações do tutor ficam salvas). O backend deve buscar as últimas mensagens e passá-las na requisição.

## Como utilizar

As requisições `POST /triage-inbound` e `POST /parse-checkin-response` passaram a aceitar um novo array opcional chamado `history`.

### Exemplo de Payload

```json
{
  "message": "estou indo, avisa a clínica",
  "history": [
    {
      "role": "user",
      "text": "meu cachorro foi atropelado"
    },
    {
      "role": "assistant",
      "text": "Os sinais relatados podem indicar uma situação de emergência e precisam de avaliação veterinária imediata."
    }
  ],
  "pet_id": "pet_123",
  "tutor_id": "tut_123"
}
```

### Regras do campo `role`
- Use `"user"` para mensagens enviadas pelo **Tutor**.
- Use `"assistant"` para mensagens que a **IA ou a Clínica** já enviaram antes.

### O que acontece por baixo dos panos?
A API formata essas mensagens e as empacota diretamente no "Prompt" antes de enviar para o modelo do Gemini, montando uma visão similar a esta para a IA:

```text
Histórico de mensagens:
User: meu cachorro foi atropelado
Assistant: Os sinais relatados podem indicar uma situação de emergência e precisam de avaliação veterinária imediata.

Contexto opcional: {"pet_id": "pet_123", "tutor_id": "tut_123"}

Mensagem atual do tutor: estou indo, avisa a clínica
```

Dessa forma, a IA conectará a resposta *"estou indo"* ao evento do *"atropelamento"* ocorrido na mensagem anterior, classificando corretamente a situação contínua como `EMERGENCIA`.
