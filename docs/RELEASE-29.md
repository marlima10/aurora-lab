# AuroraLAB 29.0.0 — cadastro concluído e chave entregue

## Falha reproduzida

O formulário oferecia Cockpit para qualquer novo e-mail, mas o servidor corretamente reservava essa permissão ao administrador principal. Ao selecionar todos os aplicativos, a API respondia “Cockpit reservado ao administrador”, cancelava o cadastro e não gerava chave. A mensagem ficava no fim da página, distante do botão, tornando a causa pouco visível.

A falha foi reproduzida pelo navegador com o handler HTTP e o Store/SQLite reais do projeto em ambiente local descartável: a lista permaneceu com um usuário e nenhuma chave foi exibida. A correção anterior de posicionamento da lista não cobria esse fluxo de cadastro com permissões.

## Correções

- `/auth/apps` declara os aplicativos exclusivos do administrador em `adminOnly`, mantendo o objeto `apps` compatível.
- Para outro e-mail, Cockpit fica desabilitado, é desmarcado se o destino mudar e recebe uma explicação na própria opção. O envio ignora permissões desabilitadas. A validação do servidor permanece ativa; nenhuma nova permissão administrativa é concedida.
- Progresso e erros aparecem junto ao botão de cadastro, com mensagens de confirmação, salvamento e conclusão.
- O botão é bloqueado antes de abrir a confirmação e liberado ao concluir/cancelar, evitando confirmações e envios duplicados.
- Requisições têm prazo de 20 segundos e tratam respostas inesperadas sem expor corpos remotos. Em caso de resposta perdida, o operador é orientado a verificar a lista antes de repetir. Não há repetição automática de emissão de chaves.
- Arquivos de acesso versionados em 29; `/auth/` permanece fora do cache offline. Banco, chaves existentes e política de administração preservados.

## Validação

- Novo teste HTTP confirma a política administrativa, recusa sem cadastro parcial e sucesso com uma permissão permitida; a chave retornada autentica o usuário correto. A suíte completa inclui também os testes anteriores de CSRF, sessões, exclusão, migração e concorrência.
- 13 cenários de DOM cobrem sete permissões permitidas, remoção da seleção Cockpit ao mudar o e-mail, erro de cadastro visível, proteção de envio duplicado e os fluxos anteriores de lista, chave e exclusão. O jsdom simula a camada de diálogo.
- **Ensaio completo no navegador com API/SQLite reais e dados fictícios:** cadastro com os sete aplicativos permitidos; contagem passou de um para dois; janela exibiu uma chave de 151 caracteres; login com essa chave reconheceu o novo perfil e mostrou sete aplicativos sem controles administrativos; administrador excluiu a conta; contagem voltou a um; a chave excluída deixou de autenticar.
- `checks/ui_fixture.py` torna esse ensaio reproduzível: banco temporário e identidades fictícias, somente loopback, sem destino de produção configurável. O adaptador HTTP/cookie é exclusivo do teste local e não participa da imagem em produção.
- Nenhum usuário real foi criado, renovado ou excluído para testar. A aplicação atualiza somente o autenticador e preserva os aplicativos nativos. Snapshot privado consistente e comparação dos registros existentes usados na implantação.

## Uso

Abra Gestão de usuários, expanda o cadastro, informe o e-mail e escolha os aplicativos disponíveis. Cockpit permanece exclusivo do administrador principal. Clique Cadastrar ou renovar chave e confirme. A chave é entregue na janela; copie antes de sair. Uma chave anterior continua irrecuperável a partir do hash: renovar gera outra e encerra a validade da anterior.

Os registros de implantação, snapshots e evidências com dados exclusivamente fictícios ficam no diretório privado do operador. A publicação segue branch rafael, PR oficial, merge na main e tag nova, preservando as releases anteriores.
