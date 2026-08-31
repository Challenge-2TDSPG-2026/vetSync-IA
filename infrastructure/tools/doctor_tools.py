def consultar_historico(tutor_name: str, pet_name: str = None) -> str:
    """Busca no banco de dados o histórico clínico, receitas e prontuários do pet do tutor informado."""
    print(f"-> [Function Calling] IA buscou histórico de: {tutor_name}, pet: {pet_name}")
    return f"Histórico de {tutor_name}: Última consulta há 2 meses. Receita: Dipirona gotas. Prontuário: Animal chegou com dores leves, mas liberado bem."
