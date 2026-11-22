# AuroraLAB 38.0.0 — Voz Antônio com ritmo calmo

O Javis passa a utilizar Antônio, voz masculina brasileira do Edge TTS gratuito. O perfil usa ritmo inicial de 0,90× e tom ligeiramente mais grave (-4 Hz), mantendo português brasileiro e a conversa Gemini existente.

- Antônio selecionado no servidor e como padrão brasileiro em instalações novas.
- Migração única do navegador aplica a voz e o ritmo. Alterações posteriores no seletor e na velocidade continuam respeitadas. A migração do perfil não troca um idioma que o usuário tenha escolhido depois da atualização anterior.
- O ajuste de tom afeta somente Antônio, preserva parâmetros explícitos de tom e não interfere nas outras vozes ou no ritmo escolhido pelo cliente.
- Arquivo da migração recebe nova versão de cache para alcançar dispositivos já abertos.
- Mantidos login central, consultas aos aplicativos, reconhecimento pt-BR, túnel TLS restrito e limites do Gemini. Nenhuma API paga ou serviço novo foi ativado.

Validação: 28 testes do módulo aprovados, incluindo aplicação do tom somente a Antônio e preservação de tom explícito e ritmo. Testes JavaScript de migração única e preservação de escolhas posteriores aprovados; opção nativa de 0,90× e sintaxe conferidas. Geração real de áudio sintético e cópia de segurança ficam registradas no relatório da implantação. O teste no servidor valida áudio e parâmetros; ouvir no aparelho continua sujeito à saída de áudio e às permissões do navegador.

Para receber o perfil, recarregue o Javis. Em Configurações > Voz, use a amostra para ouvir. O controle nativo de velocidade permite ajustar o ritmo após a migração inicial.
