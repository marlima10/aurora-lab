# AuroraLAB 27.0.0 — chave visível e exclusão de usuários

O administrador agora vê a chave recém-gerada em uma janela central, sem precisar procurar abaixo do formulário de permissões. A janela identifica o e-mail, mostra os 151 caracteres em campo selecionável e oferece Copiar chave e Fechar, com retorno de sucesso ou instrução de cópia manual.

## Ações na lista

- **Ver chave gerada:** reabre uma chave emitida durante a mesma sessão desta página. A chave fica apenas na memória da página; sair, recarregar ou navegar descarta essa cópia.
- **Gerar nova chave:** emite outra chave mantendo as permissões atuais e encerra a validade da chave/sessões anteriores. Não altera a senha de aplicativos nativos.
- **Revogar acesso:** bloqueia a chave e encerra sessões, mantendo o registro na lista.
- **Excluir usuário:** encerra o acesso e remove o cadastro da listagem. Os dados e perfis dos aplicativos permanecem preservados. A exclusão é lógica e auditada; cadastrar novamente o mesmo e-mail permite recuperar o cadastro com outra chave.

Todas as operações destrutivas de acesso e a geração exigem confirmação na própria página, com opção Cancelar. Somente o administrador central pode usar essas funções. O administrador inicial não pode ser excluído e não ganha botão de exclusão na lista.

## Persistência e segurança

A migração versionada 1 acrescenta o marcador `users.deleted` e o registro `schema_migrations` sem trocar hashes, permissões ou sessões existentes. Os inserts usam colunas explícitas para compatibilidade com o novo campo. A consulta de sessão/login e a exigência administrativa recusam cadastros excluídos. A exclusão remove sessões, incrementa a geração e mantém a auditoria e os vínculos nativos para recuperação.

A rota POST `/auth/delete` exige sessão administrativa, CSRF e origem correta. Nenhuma chave antiga passa a ser recuperável: o servidor continua armazenando apenas hashes e não devolve chaves pela listagem. Para uma chave emitida antes desta página, é necessário gerar outra. A chave inicial do administrador foi preservada e nenhuma credencial integra esta publicação.

## Validação e implantação

- **20 testes de autenticação no Linux aprovados**, com bases sintéticas: migração de banco 26 preservando chave/sessão, reexecução idempotente, exclusão de ativo/revogado, recusa de usuário comum, proteção do administrador, revogação de sessões, recuperação e proteção de CSRF/origem.
- **Oito cenários de DOM aprovados** com jsdom 30.1.3: confirmação antes da emissão, janela/campo/foco, reabertura da chave, cancelamento/renovação, cancelamento/exclusão e limpeza ao sair. O jsdom não implementa a camada visual de diálogo; o teste simula apenas seu estado aberto/fechado.
- Verificação de sintaxe JavaScript e Compose.
- Snapshot consistente do banco central anterior à mudança, integridade SQLite e cópia externa privada com SHA-256 verificados. Testes de criação/exclusão não usam usuários reais.
- Somente o autenticador é reconstruído/recriado; os demais aplicativos e seus dados permanecem preservados. Os arquivos de acesso carregam a versão 27; `/auth/` continua fora do service worker e com resposta sem cache.

A conferência interativa no navegador integrado foi limitada por uma confirmação nativa presa em uma aba de teste antiga. As confirmações atuais são diálogos da própria página; os testes de DOM e API verificam o fluxo sem modificar cadastros pessoais. O relatório operacional registra a verificação real de leitura e preservação após aplicar a mudança.

## Operação e retorno

Abra Gestão de usuários no portal com o administrador existente. Para um cadastro que já foi criado sem conseguir copiar sua chave, clique Gerar nova chave e copie a nova na janela. Excluir usuário não apaga dados do openGym, Mealie ou outros aplicativos. Chaves e permissões individuais não são concedidas automaticamente a outras identidades.

O snapshot privado, o código anterior e a imagem 26 ficam preservados para retorno planejado. Uma restauração de cadastro precisa considerar mudanças posteriores do operador; não sobrescreva um banco ativo com o snapshot. Consulte [LOGIN-UNICO.md](LOGIN-UNICO.md) e [ATUALIZACAO.md](ATUALIZACAO.md).
