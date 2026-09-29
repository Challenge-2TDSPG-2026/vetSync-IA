# Especificação — agendamento por blocos no chat SIA

**Status:** especificação concluída na Etapa 1; ainda não está disponível na API.

## Objetivo

Uma mensagem livre inicia o agendamento. As escolhas previsíveis são feitas por
blocos selecionáveis no aplicativo, para que o modelo não interprete nomes,
horários ou identificadores que já existem nos cadastros da VetSync.

O primeiro recorte atende **consulta de clínico geral**. O fluxo não confirma
diagnóstico, não prescreve e não substitui a avaliação presencial.

## Decisões do fluxo

1. O tutor escreve: `Quero marcar uma consulta amanhã`.
2. A SIA identifica a intenção de agendar e resolve a data para uma data
   absoluta no fuso `America/Sao_Paulo`.
3. A API consulta no Java os slots livres de `CLINICO_GERAL` para a data e
   responde com um bloco `SELECIONAR_HORARIO`.
4. O tutor toca em um horário. Cada opção já aponta para o veterinário e o tipo
   de evento válidos; o aplicativo não mostra nem envia esses IDs como texto.
5. A API responde com `SELECIONAR_PET`, usando somente os pets do tutor
   autenticado.
6. Após a escolha do pet, a API mostra um resumo e o bloco `CONFIRMAR_RESERVA`.
7. Somente o toque em `Confirmar reserva` chama `POST /eventos` no Java.
8. A SIA confirma a consulta somente se o Java devolver sucesso. Um conflito
   devolve novos horários; nenhuma reserva é criada antes disso.

Se o tutor solicitar outro serviço, a API mostra antes o bloco
`SELECIONAR_TIPO_ATENDIMENTO`. Somente a palavra **consulta** sem tipo explícito
usa `CLINICO_GERAL` como padrão.

```mermaid
sequenceDiagram
    actor Tutor
    participant App as Aplicativo
    participant SIA as API SIA
    participant Java as VetSync Java

    Tutor->>App: Quero marcar uma consulta amanhã
    App->>SIA: mensagem livre
    SIA->>Java: consultar slots de CLINICO_GERAL
    Java-->>SIA: slots livres reais
    SIA-->>App: bloco SELECIONAR_HORARIO
    Tutor->>App: toca em horário
    App->>SIA: sessaoId + opcaoId
    SIA->>Java: GET /pets
    Java-->>SIA: pets autorizados
    SIA-->>App: bloco SELECIONAR_PET
    Tutor->>App: toca em pet e confirma
    App->>SIA: sessaoId + opcaoId
    SIA->>Java: POST /eventos
    Java-->>SIA: evento criado ou conflito
    SIA-->>App: confirmação ou novos horários
```

## Blocos devolvidos ao aplicativo

O endpoint de chat deixará de retornar apenas `mensagem`. A resposta futura
terá texto humano e, quando aplicável, uma ação estruturada:

```json
{
  "mensagem": "Encontrei estes horários para consulta de clínico geral em 30/09.",
  "bloco": {
    "tipo": "SELECIONAR_HORARIO",
    "sessaoId": "uuid",
    "titulo": "Escolha um horário",
    "opcoes": [
      {
        "id": "slot-assinado",
        "rotulo": "09:00",
        "descricao": "Dra. Ana",
        "habilitado": true
      }
    ]
  }
}
```

Tipos de bloco da primeira versão:

| Tipo | Quando aparece | Dados exibidos |
| --- | --- | --- |
| `SELECIONAR_DATA` | A mensagem não contém data compreensível | datas sugeridas e opção de calendário |
| `SELECIONAR_TIPO_ATENDIMENTO` | O tutor pediu serviço diferente de consulta geral | tipos reais do Java |
| `SELECIONAR_HORARIO` | Há data e tipo definidos | horário e veterinário responsável |
| `SELECIONAR_PET` | Há slot escolhido | nome e espécie dos pets autorizados |
| `CONFIRMAR_RESERVA` | Há slot e pet escolhidos | pet, tipo, data, horário e veterinário |

O valor técnico de uma opção fica no servidor. O aplicativo envia somente
`sessaoId` e `opcaoId` à rota de seleção. Essa rota valida que a opção pertence
à sessão e ao tutor autenticado antes de avançar.

## Estado da sessão de agendamento

A SIA deverá manter uma sessão curta, expirada e vinculada ao tutor autenticado.
Ela contém os campos que serão usados no Java:

```text
estado: AGUARDANDO_DATA | AGUARDANDO_TIPO | AGUARDANDO_HORARIO |
        AGUARDANDO_PET | AGUARDANDO_CONFIRMACAO | CONCLUIDA | EXPIRADA
idTipoEvento: obrigatório antes de consultar slots
idVeterinario: definido pela escolha do slot
dtEvento e hrEvento: definidos pela escolha do slot
idPet: definido pelo bloco de pets
dsObservacao: opcional, informada em texto livre
```

Uma seleção direta não chama o orquestrador. O modelo pode ser usado apenas na
entrada livre para reconhecer que o tutor quer agendar, extrair a data ou
entender uma observação que não faça parte de uma escolha estruturada.

## Contratos necessários

### Java — disponibilidade real

Criar uma consulta autenticada de slots, proposta como:

```text
GET /agenda/slots?data=YYYY-MM-DD&categoria=CLINICO_GERAL
```

Resposta proposta:

```json
{
  "data": "2026-09-30",
  "slots": [
    {
      "idTipoEvento": 8,
      "idVeterinario": 4,
      "nmVeterinario": "Dra. Ana",
      "hrEvento": "09:00"
    }
  ]
}
```

O Java deve calcular esses slots com a disponibilidade semanal do veterinário,
bloqueios e eventos `AGENDADO`. O tamanho de cada atendimento deve ser uma
configuração real do tipo de evento; não será assumido pela SIA. A categoria
`CLINICO_GERAL` deve ser um valor cadastrado em `dsCategoria`, sem depender de
comparação pelo nome do tipo de evento.

`POST /eventos` permanece a única operação que cria a consulta. Ele precisa
revalidar bloqueio e conflito no momento da criação e devolver `409` quando o
slot tiver sido ocupado.

### SIA — início e seleções

O endpoint de conversa permanece a entrada de texto livre. A implementação
poderá manter `POST /api/v1/ia/orquestrador/processar` para isso, agora com o
campo opcional `bloco` na resposta.

As escolhas dos blocos terão uma rota sem modelo, proposta como:

```text
POST /api/v1/ia/agendamentos/sessoes/{sessaoId}/selecoes
{
  "opcaoId": "slot-assinado"
}
```

Cada resposta dessa rota tem o mesmo formato de `mensagem` e `bloco`. A última
confirmação realiza o `POST /eventos` com o Bearer original do tutor.

## Regras de segurança e falha

- O Java continua validando a posse do pet pelo JWT; a SIA não é autoridade de
  autorização.
- IDs de pet, tipo e veterinário recebidos pelo aplicativo nunca são aceitos
  sem validação contra a sessão e os dados atuais do Java.
- Uma sessão expirada ou uma opção inválida reinicia a etapa afetada com dados
  atualizados.
- Se não houver slots, o bloco mostra uma data alternativa obtida do Java ou
  informa claramente a ausência de disponibilidade.
- Se uma mensagem trouxer sintomas e pedido de consulta, a SIA envia uma
  orientação curta para avaliação presencial e mantém o fluxo de agendamento.
  Ela não classifica urgência, diagnostica nem recomenda medicamento.

## Limites atuais confirmados

- O Java já possui disponibilidade semanal, bloqueios e validação de conflito
  em `POST /eventos`, mas não possui uma rota que calcule slots livres.
- O contrato atual de `GET /tipos-evento` expõe `dsCategoria`, mas não define
  `CLINICO_GERAL` como categoria de negócio nem uma duração por tipo.
- A resposta atual do chat é somente `{ "mensagem": "..." }`; o aplicativo
  ainda não recebe nem renderiza blocos.
- A ferramenta Python `consultar_disponibilidade` contém horários fixos e não
  participa do contrato futuro.
