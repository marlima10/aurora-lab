# Login único AuroraLAB

## Estado e responsabilidade

Implementação introduzida na release 24 e migrada/validada no AuroraServer na release 25. Em outras instalações, não é ativada ao atualizar o portal. É necessário validar cada integração antes de trocar os acessos ativos. `ready: false` bloqueia o aplicativo; não use `true` como atalho para pular testes.

O usuário entra com e-mail e chave de 151 caracteres no HTTPS principal. A mesma sessão autoriza aplicativos no mesmo hostname, em portas diferentes. A sessão dura até 12 horas. O administrador tem o atalho 👥 Gestão de usuários na página principal; usuários comuns não veem esse atalho e não acessam a API administrativa. Não há envio automático de e-mails: o administrador copia a nova chave e a distribui ao titular.

Somente `aurora@server.local` cadastra, gera/renova, copia no momento da geração e revoga chaves. O banco guarda hashes. Renovar a chave encerra sessões existentes daquele cadastro. O botão “Sair de todos os aplicativos” encerra a sessão central do navegador atual; não encerra sessões de outros aparelhos.

## Preparação sem ativação

1. Faça backup verificado, registre a configuração Compose/Tailscale e mantenha o SSH por chave funcionando. Não remova volumes nem substitua `.env`, `secrets/` ou `data/`.
2. Requer Compose com suporte a `!reset`/`!override` (2.24.4 ou posterior), HTTPS privado existente, as contas nativas e a imagem HomeBoard fixada já construída.
3. Crie como root um inventário privado fora do Git, com `apps` e `admin_grants`. O inventário contém os oito aplicativos: `manyfold`, `mealie`, `actual`, `opengym`, `octoprint`, `homeassistant`, `homeboard`, `cockpit`.
4. Para cada aplicativo, `identities` é um objeto de identificadores existentes; `labels` contém nomes legíveis. Manyfold/Mealie usam e-mail existente; openGym e HA usam IDs internos; OctoPrint usa usuário existente; HomeBoard usa `viewer`/`editor`; Actual usa um identificador de acesso à instância compartilhada. Cockpit usa a conta Debian existente, sem mapear `root`.
5. Para HA, os valores de `identities` são aliases únicos do bloco `198.18.0.0/24`, por exemplo `198.18.0.10`; nos demais aplicativos os valores podem repetir o identificador. `admin_grants` escolhe uma identidade existente em cada aplicativo. Conferir essas escolhas significa autorizar acesso àqueles dados.

Exemplo estrutural parcial (o inventário real deve incluir os oito aplicativos):

```json
{
  "apps": {
    "opengym": {"identities": {"ID_EXISTENTE": "ID_EXISTENTE"}, "labels": {"ID_EXISTENTE": "Meu perfil"}},
    "homeassistant": {"identities": {"UUID_EXISTENTE": "198.18.0.10"}}
  },
  "admin_grants": {"opengym": "ID_EXISTENTE", "homeassistant": "UUID_EXISTENTE"}
}
```

Execute na raiz real da instalação:

```sh
sudo python3 docker/server/auth/prepare.py --root "$PWD" --mappings /CAMINHO/PRIVADO/inventario.json
```

O resultado informa o caminho privado da chave, sem imprimi-la. A preparação é idempotente e não renova automaticamente o administrador existente. Copie a chave inicial por canal privado. Nunca inclua o arquivo em uma issue, PR, release ou imagem Docker.

A senha atual do Actual deve corresponder à credencial privada usada na preparação. Se ela foi alterada desde a instalação, revise a origem privada antes de preparar; não redefina a senha nem o orçamento para fazer o teste passar.

## Migração controlada

Construa as imagens e valide o Compose com **todos os overlays já usados**, acrescentando `compose.auth.yaml` por último. Não substitua a seleção existente por um exemplo incompleto. Preserve o override do Tailscale. Confira os dispositivos USB antes de selecionar o overlay da impressora e o perfil da câmera: um caminho ausente impede a criação do contêiner. Se estiverem desconectados, registre a seleção anterior e suspenda somente a seleção do hardware até a reconexão; preserve dados e configurações. O Dockerfile do HomeBoard pressupõe a imagem local da revisão fixada; o preparador existente do HomeBoard deve construí-la antes, quando necessário.

Antes de ativar:

- Confirme que a rede `172.31.248.0/29` e o grupo/GID `aurora-sso:64024` não colidem com recursos existentes.
- Manyfold: conferir o usuário e seus papéis com o middleware ativo em uma cópia isolada.
- Mealie: conferir usuário existente e acesso sem formulário de senha; cadastro automático deve continuar desativado.
- Actual: testar cabeçalho nativo no orçamento de ensaio. A imagem adaptada 25 corrige a descoberta de `header` nas duas rotas de métodos da revisão 26.10.0, sem alterar o banco; a verificação de hash recusa fontes diferentes. Confira também no navegador que não aparece um segundo formulário. Autorizar o aplicativo concede acesso à instância compartilhada.
- openGym/Garmin: confirmar o perfil e treinos existentes e uma chamada de sincronização sem criar perfil novo ou duplicar exercícios. Não teste importação escrevendo em banco pessoal sem backup.
- OctoPrint: `trustRemoteUser: true`, `remoteUserHeader: X-Aurora-Identity`, `addRemoteUsers: false`, `trustRemoteGroups: false`; preserve API keys internas e permissões nativas. Testar leitura com a impressora desconectada da instância de ensaio; não enviar movimento, aquecimento ou impressão.
- HomeBoard: testar `viewer` e `editor`, incluindo recusa de escrita para o primeiro.
- Cockpit: preparar o grupo e diretório `/run/auroralab-cockpit`; instalar as unidades revisadas de `secrets/sso/host/` e a configuração de `secrets/sso/cockpit/`. A unidade usa a conta local existente e `PAMName=cockpit`, com socket Unix 0660 e diretório 0750. Copie `secrets/sso/cockpit/cockpit.conf` para `/etc/auroralab-cockpit-sso/cockpit/cockpit.conf`: o subdiretório `cockpit/` é necessário dentro de `XDG_CONFIG_DIRS`. Esse arquivo não contém senha e precisa ser legível pela conta local, mantendo propriedade root. Executar tmpfiles antes de iniciar o socket. Não publicar esse socket por TCP, não desabilitar PAM, não usar root ou NOPASSWD. O gateway usa o mesmo GID 64024. O tmpfs do Nginx deve ser montado em `/run`, pois `/var/run` é um link para esse diretório na imagem; montar no link oculta o socket privado filho. Após validar o novo acesso, desative o socket/proxy TCP legado para impedir um caminho alternativo.

### Home Assistant

O HA em rede host deve deixar de escutar publicamente em 8123: configurar porta nativa **18123**, vinculada somente ao loopback e a **172.31.248.1**. Essa interface só existe após criar a rede dedicada. O intermediário `ha-sso`, **172.31.248.2**, é o único proxy confiável. Preservar todos os demais campos da configuração e validar a sintaxe com a imagem HA instalada antes de reiniciar.

Nas versões recentes do HA, como 2026.10, a configuração HTTP já migrada é mantida em `.storage/http`; um novo bloco `http:` no YAML pode ser ignorado. Faça backup, confira o esquema HTTP da versão instalada e ajuste os campos estáveis de porta, interfaces, `use_x_forwarded_for` e `trusted_proxies`, sem sobrescrever os demais campos. Não trate esse armazenamento como um contrato genérico entre versões. Nesta instalação foram usados `server_port: 18123`, `server_host: [127.0.0.1, 172.31.248.1]` e `trusted_proxies: [172.31.248.2]`. Valide as interfaces realmente abertas após reiniciar.

O provedor de autenticação continua no YAML, mesclado aos campos existentes sem duplicar chaves:

```yaml
homeassistant:
  auth_providers:
    - type: trusted_networks
      trusted_networks: [198.18.0.0/24]
      trusted_users:
        198.18.0.10: [UUID_EXISTENTE]
      allow_bypass_login: true
    - type: homeassistant
```

Confirme que não existe outra instância HA ocupando 8123. Na migração do AuroraServer, uma instância antiga em `/DATA/AppData` foi copiada e desativada, sem apagar seus dados.

O endereço do proxy não faz parte das redes de autenticação: ele encaminha o alias do usuário validado. Não confiar na LAN inteira. O intermediário verifica o proprietário do token em HTTP e WebSocket, usando um canal separado para a consulta interna de identidade, preservando os IDs crescentes do canal do navegador. A negociação de compressão WebSocket é independente e os formulários de renovação/revogação do navegador são preservados. Ele recusa tokens de outro usuário. Um navegador com sessão antiga de outro usuário pode precisar sair dessa sessão nativa uma vez durante a migração.

### Troca do gateway

Somente depois de validar cada integração, registre `ready: true` no arquivo privado daquele aplicativo. Recrie o auth para carregar o inventário atualizado. Não libere uma aplicação ainda não ensaiada.

O HTTPS principal passa a encaminhar ao gateway em `127.0.0.1:18080`. As portas HTTPS dos aplicativos encaminham às respectivas portas de loopback do novo gateway. Cockpit deve encaminhar **HTTP** ao gateway em `127.0.0.1:9090`, pois a terminação TLS fica no Tailscale; o proxy TLS antigo não pode manter a mesma publicação de porta.

Atualize somente os destinos necessários do Tailscale Serve. Não use reset global, não ative Funnel e não exponha o serviço `auth:7777`. HTTP nas portas 80/8088 só redireciona ao HTTPS fixo. Verifique de outro aparelho que nenhuma porta nativa/monitor permite contornar o gateway, incluindo HA 18123 e Cockpit nativo anterior. Preserve acesso local/SSH de recuperação.

## Validação de aceitação e retorno

Teste um navegador sem sessão, administrador e usuário comum; todos os oito aplicativos; recusa por falta de permissão; perfil correto; rotação, revogação e saída; energia sem chave adicional; backup e restauração isolada com `auth.sqlite3`.

No retorno, restaure a seleção Compose, portas nativas, configuração HA e destinos Serve registrados antes da migração. Desative apenas as novas unidades do socket SSO do Cockpit. Preserve o banco central e os segredos para investigar; nunca apague dados ou faça `down -v`. Os mecanismos nativos originais continuam disponíveis após restaurar a configuração anterior.

As fontes oficiais de referência são [Actual](https://actualbudget.org/docs/advanced/http-header-auth/), [HA](https://www.home-assistant.io/docs/authentication/providers/), [Cockpit](https://cockpit-project.org/guide/latest/cockpit-ws.8.html) e [OctoPrint](https://docs.octoprint.org/en/main/configuration/config_yaml.html). Os adaptadores AuroraLAB são mantidos por este projeto e exigem nova revisão ao trocar as imagens fixadas.

No modo SSO, as páginas, scripts e API do Fitness legado ficam reservados ao administrador, pois usam registros compartilhados. O contrato dos dados permanece preservado.

## Monitoramento e migração 25

No modo SSO, o monitor consulta a API OctoPrint em `http://127.0.0.1:15000`, com a chave interna já existente. Esse destino não é publicado na LAN e evita que o monitor receba HTML do login na porta web protegida. O monitor na porta 9101 exige o segredo privado configurado; o portal o injeta somente no servidor.

O cache PWA 25 verifica a sessão antes da instalação: usuários comuns não tentam guardar os arquivos Fitness reservados ao administrador. Redirecionamentos de login não são gravados como HTML ou JavaScript offline. `/auth/` continua fora do cache. A instalação portátil sem SSO continua compatível.

A [release 25](RELEASE-25.md) registra a aceitação real e os limites da migração, sem publicar dados ou credenciais.

## Gestão de usuários — release 27

Depois de cadastrar ou renovar, uma janela abre com a chave completa, e-mail destinatário, campo selecionável e botão Copiar chave. Fechar limpa o campo; a lista oferece Ver chave gerada enquanto essa página continua aberta. Recarregar, sair ou navegar limpa a memória da página. Chaves antigas não podem ser recuperadas do hash; use Gerar nova chave para substituí-las. O botão de renovação na lista mantém as permissões atuais e encerra a chave/sessões antigas. A confirmação na própria página permite cancelar antes de qualquer alteração.

Excluir usuário retira o cadastro da lista e encerra seu acesso central, sem apagar perfis ou dados dos aplicativos. A exclusão é lógica e auditada; cadastrar novamente o mesmo e-mail emite outra chave e recupera o cadastro. O administrador inicial é protegido. Rotas de cadastro, exclusão e geração são administrativas e exigem CSRF/origem correta. Não é possível consultar chaves históricas em texto puro.
