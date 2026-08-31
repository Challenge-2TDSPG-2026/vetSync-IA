import os
from dotenv import load_dotenv
from infrastructure.gemini_gateway import GeminiGateway

load_dotenv()

gateway = GeminiGateway()

print("Testando Agendamento (que usa a tool separada)...")
response = gateway.parse_scheduling_intent("Gostaria de agendar uma consulta para o meu pet amanhã de manhã")
print("Resultado Agendamento:", response)

print("\nTestando Comando do Médico (que usa a tool separada)...")
response_doc = gateway.parse_doctor_command("Puxe o histórico do Rex do tutor Joao")
print("Resultado Médico:", response_doc)
