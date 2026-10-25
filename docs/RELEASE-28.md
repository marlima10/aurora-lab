# AuroraLAB 28.0.0 — lista administrativa visível no topo

A lista de cadastros ficava depois do formulário completo de permissões, abaixo dos atalhos de aplicativos. Isso dificultava encontrá-la e dava a impressão de que não havia usuários. A área administrativa agora aparece antes dos atalhos e mostra a lista e sua quantidade logo no início.

## Mudanças

- Lista Usuários cadastrados no topo, com contador e identificação do administrador principal.
- Botão Atualizar lista, indicação de carregamento e erro visível com orientação de nova tentativa. Falhas não apagam a última lista disponível.
- Cadastro em uma seção expansível separada, preservando os campos, permissões e confirmação de geração da chave.
- Orientação explícita de que o cadastro aparece somente após confirmar a operação; indicação de campos inválidos/obrigatórios.
- Arquivos da área de acesso versionados em 28; rotas `/auth/` continuam fora do cache PWA e com no-store.

Apenas o administrador central vê a lista. Esta versão não cria usuários, renova chaves, muda permissões, exclui cadastros ou altera o banco. As funções da release 27 permanecem disponíveis.

## Validação

Dez cenários de DOM com dados fictícios verificam posição/contador da lista, falha e recuperação, confirmação, exibição e reabertura de chave, cancelamento/renovação, cancelamento/exclusão e logout. O jsdom simula apenas a camada de diálogo, não implementada na biblioteca. JavaScript e Compose conferidos.

Antes da mudança, a API real respondeu normalmente e o formulário real foi conferido até sua confirmação, cancelada sem gravar usuário de teste. A implantação recria somente o autenticador, mantendo banco e chave atuais. Não é necessária migração de esquema. O relatório operacional registra a conferência visual após aplicar a alteração, contagens e snapshots privados, sem expor credenciais.
