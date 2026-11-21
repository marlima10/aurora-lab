"""The model sees only these explicit operations, never application credentials."""
def tool(name, description, properties=None, required=()):
    return {'type': 'function', 'function': {'name': name, 'description': description,
        'parameters': {'type': 'object', 'properties': properties or {}, 'required': list(required), 'additionalProperties': False}}}

S = {'type': 'string'}
TOOLS = [
    tool('notes_list', 'Consultar minhas notas pessoais.'),
    tool('note_save', 'Propor salvar uma nota; o usuário precisa confirmar.', {'content': S}, ['content']),
    tool('reminders_list', 'Consultar minha caixa de lembretes.'),
    tool('reminder_create', 'Propor lembrete na caixa Jarvis. Não é push no celular. Horário ISO com fuso obrigatório.', {'content': S, 'due': S}, ['content', 'due']),
    tool('report_save', 'Propor salvar um relatório Markdown com fontes. Não invente fontes.', {'content': S}, ['content']),
    tool('fitness_summary', 'Resumo real dos treinos openGym por intervalo YYYY-MM-DD; para últimos cinco, usar limit 5.', {'start': S, 'end': S, 'limit': {'type': 'integer', 'minimum': 1, 'maximum': 100}}, ['start', 'end']),
    tool('finance_accounts', 'Consultar as contas do orçamento autorizado.'),
    tool('finance_summary', 'Consultar totais reais de receitas e despesas entre datas YYYY-MM-DD.', {'start': S, 'end': S}, ['start', 'end']),
    tool('finance_add_transaction', 'Propor despesa ou receita. Valor inteiro em centavos: negativo para despesa; conta e categoria devem vir dos dados reais.',
         {'accountId': S, 'date': S, 'amount': {'type': 'integer'}, 'payee': S, 'categoryId': S, 'notes': S}, ['accountId', 'date', 'amount', 'payee']),
    tool('food_recipes', 'Buscar minhas receitas Mealie.', {'query': S}),
    tool('food_shopping_lists', 'Consultar listas de compras Mealie.'),
    tool('food_add_recipe', 'Propor criar uma receita pelo nome no Mealie.', {'name': S}, ['name']),
    tool('print_status', 'Consultar estado e progresso atuais no OctoPrint.'),
    tool('print_library', 'Consultar modelos da biblioteca Manyfold.', {'query': S}),
    tool('print_pause', 'Propor pausar uma impressão. Nunca inicia nem alterna o estado automaticamente.'),
    tool('research_search', 'Pesquisar informações públicas na internet. Não enviar dados privados ou pessoais na consulta.', {'query': S}, ['query']),
]
WRITE_TOOLS = {'note_save', 'reminder_create', 'report_save', 'finance_add_transaction', 'food_add_recipe', 'print_pause'}
APP_TOOLS = {'fitness_summary': 'opengym', 'finance_accounts': 'actual', 'finance_summary': 'actual',
             'finance_add_transaction': 'actual', 'food_recipes': 'mealie', 'food_shopping_lists': 'mealie',
             'food_add_recipe': 'mealie', 'print_status': 'octoprint', 'print_pause': 'octoprint', 'print_library': 'manyfold'}


def available(session):
    return [t for t in TOOLS if APP_TOOLS.get(t['function']['name'], 'portal') in session['grants']
            and (t['function']['name'] != 'research_search' or session.get('allow_web_search') is True)]


def validate(name, args, session):
    from common import Problem
    choices = {t['function']['name']: t['function']['parameters'] for t in available(session)}
    if name not in choices or not isinstance(args, dict):
        raise Problem(403, 'Ferramenta não autorizada para este usuário.')
    schema = choices[name]
    if set(args) - set(schema['properties']) or set(schema['required']) - set(args):
        raise Problem(400, 'Argumentos incompletos ou inesperados.')
    for key, value in args.items():
        kind = schema['properties'][key]['type']
        if (kind == 'string' and (not isinstance(value, str) or len(value) > 12000)) or (kind == 'integer' and (isinstance(value, bool) or not isinstance(value, int))):
            raise Problem(400, 'Tipo de argumento inválido.')
