# Login único AuroraLAB

## Estado e responsabilidade

Implementação opcional da release 24. Não é ativada ao atualizar o portal. É necessário validar cada integração antes de trocar os acessos ativos. `ready: false` bloqueia o aplicativo; não use `true` como atalho para pular testes.

O usuário entra com e-mail e chave de 151 caracteres no HTTPS principal. A mesma sessão autoriza aplicativos no mesmo hostname, em portas diferentes. A sessão dura até 12 horas. Não há envio automático de e-mails: o administrador copia a nova chave e a distribui ao titular.

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

Construa as imagens e valide o Compose com **todos os overlays já usados**, acrescentando `compose.auth.yaml` por último. Não substitua a seleção existente por um exemplo incompleto. Preserve os perfis da câmera/impressora e o override do Tailscale. O Dockerfile do HomeBoard pressupõe a imagem local da revisão fixada; o preparador existente do HomeBoard deve construí-la antes, quando necessário.

Antes de ativar:

- Confirme que a rede `172.31.248.0/29` e o grupo/GID `aurora-sso:64024` não colidem com recursos existentes.
- Manyfold: conferir o usuário e seus papéis com o middleware ativo em uma cópia isolada.
- Mealie: conferir usuário existente e acesso sem formulário de senha; cadastro automático deve continuar desativado.
- Actual: testar cabeçalho nativo no orçamento de ensaio. Autorizar o aplicativo concede acesso à instância compartilhada.
- openGym/Garmin: confirmar o perfil e treinos existentes e uma chamada de sincronização sem criar perfil novo ou duplicar exercícios. Não teste importação escrevendo em banco pessoal sem backup.
- OctoPrint: `trustRemoteUser: true`, `remoteUserHeader: X-Aurora-Identity`, `addRemoteUsers: false`, `trustRemoteGroups: false`; preserve API keys internas e permissões nativas. Testar leitura com a impressora desconectada da instância de ensaio; não enviar movimento, aquecimento ou impressão.
- HomeBoard: testar `viewer` e `editor`, incluindo recusa de escrita para o primeiro.
- Cockpit: preparar o grupo e diretório `/run/auroralab-cockpit`; instalar as unidades revisadas de `secrets/sso/host/` e a configuração de `secrets/sso/cockpit/`. A unidade usa a conta local existente e `PAMName=cockpit`, com socket Unix 0660 e diretório 0750. Executar tmpfiles antes de iniciar o socket. Não publicar esse socket por TCP, não desabilitar PAM, não usar root ou NOPASSWD. O gateway usa o mesmo GID 64024.

### Home Assistant

O HA em rede host deve deixar de escutar publicamente em 8123: configurar porta nativa **18123**, vinculada somente ao loopback e a **172.31.248.1**. Essa interface só existe após criar a rede dedicada. O intermediário `ha-sso`, **172.31.248.2**, é o único proxy confiável. Preservar todos os demais campos da configuração e validar a sintaxe com a imagem HA instalada antes de reiniciar.

Configuração conceitual — mesclar com os campos existentes, sem criar chaves YAML duplicadas:

```yaml
http:
  server_port: 18123
  server_host: [127.0.0.1, 172.31.248.1]
  use_x_forwarded_for: true
  trusted_proxies: [172.31.248.2]
homeassistant:
  auth_providers:
    - type: trusted_networks
      trusted_networks: [198.18.0.0/24]
      trusted_users:
        198.18.0.10: [UUID_EXISTENTE]
      allow_bypass_login: true
    - type: homeassistant
```

O endereço do proxy não faz parte das redes de autenticação: ele encaminha o alias do usuário validado. Não confiar na LAN inteira. O intermediário verifica o proprietário do token em HTTP e WebSocket e recusa tokens de outro usuário. Um navegador com sessão antiga de outro usuário pode precisar sair dessa sessão nativa uma vez durante a migração.

### Troca do gateway

Somente depois de validar cada integração, registre `ready: true` no arquivo privado daquele aplicativo. Recrie o auth para carregar o inventário atualizado. Não libere uma aplicação ainda não ensaiada.

O HTTPS principal passa a encaminhar ao gateway em `127.0.0.1:18080`. As portas HTTPS dos aplicativos encaminham às respectivas portas de loopback do novo gateway. Cockpit deve encaminhar **HTTP** ao gateway em `127.0.0.1:9090`, pois a terminação TLS fica no Tailscale; o proxy TLS antigo não pode manter a mesma publicação de porta.

Atualize somente os destinos necessários do Tailscale Serve. Não use reset global, não ative Funnel e não exponha o serviço `auth:7777`. HTTP nas portas 80/8088 só redireciona ao HTTPS fixo. Verifique de outro aparelho que nenhuma porta nativa/monitor permite contornar o gateway, incluindo HA 18123 e Cockpit nativo anterior. Preserve acesso local/SSH de recuperação.

## Validação de aceitação e retorno

Teste um navegador sem sessão, administrador e usuário comum; todos os oito aplicativos; recusa por falta de permissão; perfil correto; rotação, revogação e saída; energia sem chave adicional; backup e restauração isolada com `auth.sqlite3`.

No retorno, restaure a seleção Compose, portas nativas, configuração HA e destinos Serve registrados antes da migração. Desative apenas as novas unidades do socket SSO do Cockpit. Preserve o banco central e os segredos para investigar; nunca apague dados ou faça `down -v`. Os mecanismos nativos originais continuam disponíveis após restaurar a configuração anterior.

As fontes oficiais de referência são [Actual](https://actualbudget.org/docs/advanced/http-header-auth/), [HA](https://www.home-assistant.io/docs/authentication/providers/), [Cockpit](https://cockpit-project.org/guide/latest/cockpit-ws.8.html) e [OctoPrint](https://docs.octoprint.org/en/main/configuration/config_yaml.html). Os adaptadores AuroraLAB são mantidos por este projeto e exigem nova revisão ao trocar as imagens fixadas.

No modo SSO, as páginas, scripts e API do Fitness legado ficam reservados ao administrador, pois usam registros compartilhados. O contrato dos dados permanece preservado.
