# TI Help

Uma base de conhecimento para organizar a rotina do setor de TI.

> **Espaço para a capa do projeto** — imagem a ser enviada pelo autor.

<!-- CAPA: substitua URL_DA_CAPA pelo endereço direto da imagem no seu site
 e remova este comentário para exibir a imagem.
![Capa do projeto TI Help](URL_DA_CAPA)
-->

## Sobre o projeto

O **TI Help** é um aplicativo desktop para Windows que reúne problemas, soluções, contatos e documentação técnica em um único lugar. Ele ajuda a equipe de TI a consultar informações usadas no atendimento e registrar o conhecimento adquirido durante o trabalho.

O sistema usa um banco SQLite local e possui autenticação de usuários, permissões administrativas e uma interface escura desenvolvida com CustomTkinter. O projeto também é utilizado para estudo de Python, com o código organizado em camadas para facilitar o entendimento e a manutenção.

## O que o TI Help faz

- **Base de conhecimento:** cadastro e consulta de problemas e suas soluções.
- **Busca e categorias:** organização dos conteúdos para facilitar a pesquisa.
- **Favoritos e recentes:** acesso aos conteúdos marcados e vistos recentemente.
- **Contatos:** cadastro de telefones e informações de contato.
- **Cofre de Acessos:** área de acessos protegida por senha.
- **Documentação técnica:** registros de relatórios, telas Senior, tabelas de banco e regras.
- **Usuários Sapiens:** cadastro e consulta de informações desses usuários.
- **Usuários e permissões:** autenticação, administração de contas e recuperação de senhas com aprovação.
- **Backup:** cópia do banco de dados para preservar as informações locais.

## Imagens do programa

### 1. Tela inicial e navegação

> **Espaço para a imagem 1** — visão geral do programa em funcionamento.

<!-- IMAGEM 1: substitua URL_DA_IMAGEM_1 pelo endereço direto no seu site
 e remova este comentário para exibir a imagem.
![Tela inicial e navegação do TI Help](URL_DA_IMAGEM_1)
-->

### 2. Base de conhecimento

> **Espaço para a imagem 2** — exemplo de consulta ou cadastro de uma solução.

<!-- IMAGEM 2: substitua URL_DA_IMAGEM_2 pelo endereço direto no seu site
 e remova este comentário para exibir a imagem.
![Base de conhecimento do TI Help](URL_DA_IMAGEM_2)
-->

### 3. Recursos do sistema

> **Espaço para a imagem 3** — exemplo de outro recurso do programa.

<!-- IMAGEM 3: substitua URL_DA_IMAGEM_3 pelo endereço direto no seu site
 e remova este comentário para exibir a imagem.
![Recursos do TI Help em funcionamento](URL_DA_IMAGEM_3)
-->

## Tecnologias utilizadas

| Tecnologia | Papel no projeto |
| --- | --- |
| Python | Linguagem da aplicação e das regras de negócio. |
| CustomTkinter | Construção da interface gráfica desktop. |
| SQLite | Armazenamento local dos dados. |
| Pillow | Manipulação de imagens usadas na interface. |
| PyInstaller | Geração do pacote executável para Windows. |
| unittest | Testes automatizados das funcionalidades. |

## Como baixar e testar no Windows

O executável pronto está na pasta **[dist/TI Help](dist/TI%20Help)**. Para testar essa versão, não é necessário instalar Python.

1. Baixe o repositório pelo GitHub em **Code → Download ZIP** e extraia o arquivo, ou faça o clone com Git:

   ```powershell
   git clone https://github.com/DenilsomLobo/TI-Help.git
   cd TI-Help
   ```

2. Abra a pasta `dist/TI Help`.
3. Execute **`TI Help.exe`**.
4. Na primeira abertura, cadastre seu administrador com nome, usuário e senha.
5. Comece a cadastrar e consultar os conteúdos do sistema.

Mantenha toda a pasta `TI Help` junta, incluindo `_internal`, que contém as bibliotecas e os recursos do programa. Para usar em outro computador Windows, copie essa pasta inteira para um local com permissão de escrita.

O pacote é distribuído sem contas ou cadastros. Na primeira execução, o banco é criado em `dist/TI Help/data/ti_help.db`. Cada cópia do aplicativo mantém seu próprio banco local.

## Como instalar e executar pelo código-fonte

Para desenvolver ou estudar o projeto, instale **Python 3.11 ou mais recente** no Windows. Se utilizar o comando de clone abaixo, instale também o Git.

```powershell
 git clone https://github.com/DenilsomLobo/TI-Help.git
 cd TI-Help
 python -m venv .venv
 .\.venv\Scripts\python.exe -m pip install -r requirements.txt
 .\.venv\Scripts\python.exe main.py
```

O ambiente virtual `.venv` mantém as dependências do projeto separadas das demais instalações Python do computador. Os comandos usam diretamente o Python desse ambiente, sem precisar ativá-lo no PowerShell.

Nesta forma de execução, o banco é criado em `data/ti_help.db` na raiz do projeto. O cadastro do primeiro administrador também acontece pela interface.

## Como executar os testes

Depois de instalar as dependências, execute na raiz do projeto:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -v
```

## Como gerar um novo executável

Com o ambiente virtual criado, execute na raiz do projeto:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-build.txt
.\.venv\Scripts\python.exe -m PyInstaller --clean --noconfirm TIHelp.spec
```

O pacote será gerado em `dist/TI Help`. O banco de dados não é incorporado à compilação. Se você já usou essa pasta para testar o aplicativo, mantenha os dados locais fora do pacote que será compartilhado.

## Organização do código

```text
app/
  database/      Inicialização e migrações do banco
  models/        Estruturas e entidades
  repositories/  Consultas e gravações no SQLite
  services/      Regras de negócio
  ui/            Interface gráfica
  utils/         Funções e recursos auxiliares
assets/          Imagens, ícone e fonte
tests/           Testes automatizados
dist/            Pacote pronto para Windows
main.py          Ponto de entrada da aplicação
TIHelp.spec      Configuração do empacotamento
```

A interface chama os serviços, que aplicam as regras de negócio e utilizam os repositórios para acessar o SQLite. Essa separação mantém o SQL fora das telas e facilita a manutenção e os testes.

## Dados e segurança

- As senhas de autenticação são armazenadas com hash PBKDF2-SHA256.
- O aplicativo distribuído não possui usuário ou senha padrão.
- Bancos SQLite, pastas `data` e backups locais são ignorados pelo Git.
- O executável e suas dependências em `dist` podem acompanhar o repositório.
- Mantenha seus backups em local seguro e não compartilhe a pasta `data` criada durante o uso do aplicativo.
