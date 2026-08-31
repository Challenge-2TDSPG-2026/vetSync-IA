def consultar_disponibilidade(data_referencia: str) -> list[str]:
    """Consulta a disponibilidade de horários na agenda da clínica para uma determinada data. Ex: 'hoje', 'amanha', '2025-10-10'."""
    print(f"-> [Function Calling] IA consultou a data: {data_referencia}")
    data_lower = data_referencia.lower()
    if "hoje" in data_lower:
        return ["14:00", "15:30", "17:00"]
    elif "amanh" in data_lower:
        return ["09:00", "11:00"]
    else:
        return ["10:00", "13:00", "16:00"]
