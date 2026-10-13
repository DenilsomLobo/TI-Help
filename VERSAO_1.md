# Publicação da versão 1.0.0

Data: 13/10/2026.

## Alterações

- Preparação dos arquivos atuais como primeiro commit, sem commits pais.
- Substituição da branch `main` do GitHub, conforme autorização do proprietário.
- Identificação da versão com a tag `v1.0.0`.
- Inclusão de `.gitattributes` para preservar os arquivos de `dist` sem
  conversão automática de fim de linha durante o clone.

Nenhuma função da aplicação ou estrutura do banco foi modificada nesta etapa.
O pacote Windows e suas dependências acompanham o código. Bancos, backups e
ambientes virtuais permanecem fora do versionamento.

## Verificação

Antes do envio, foram conferidos o remoto, a ausência de commits na branch
inicial, os arquivos preparados e as dependências do pacote. O repositório
remoto possuía apenas `main`, sem outras branches ou tags.

O envio utiliza `--force-with-lease` com o identificador esperado da `main`
remota: se alguém modificar a branch durante a operação, o Git interrompe o
envio em vez de sobrescrever essa mudança.

Após publicar, confira o commit inicial e a tag no GitHub. Para testar o
programa, clone ou baixe o repositório e abra `dist/TI Help/TI Help.exe`.

A troca da branch retira o histórico anterior da navegação normal da `main`.
Ela não garante a eliminação imediata de objetos antigos dos servidores,
cópias locais ou forks existentes.
