# wger — avaliação encerrada

O proprietário encerrou o teste na release 46 e optou por continuar com o openGym/Garmin.

Foram removidos o projeto Docker de avaliação, seus containers/redes, imagens específicas, banco, uploads, cópia de importação, credenciais, fontes implantadas e rota HTTPS :8444. Os dumps/pacotes específicos do wger foram excluídos, e o backup misto foi higienizado sem alterar os arquivos dos outros aplicativos.

O Compose e os adaptadores anteriores não existem mais no código atual. O histórico Git e a release 45 permanecem como registro, sem reescrita. Não tente iniciar o instalador antigo no ambiente atual.

O openGym e a sincronização Garmin permanecem nos serviços existentes. Consulte [RELEASE-46.md](RELEASE-46.md).
