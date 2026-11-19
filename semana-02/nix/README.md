# Parte do integrante 3 — Nix

## Material pronto e ordem de leitura

1. [Relatório e respostas às cinco perguntas](./relatorio-nix.md): texto para a pesquisa e fundamentação da apresentação.
2. Este arquivo: procedimento da demonstração, roteiro de fala e conteúdo sugerido para slides.
3. [Validação prática](./evidencias/validacao.md): resultados obtidos pelo terminal e pendências.

O exemplo é o **GNOME Text Editor**, o mesmo escolhido para os demais gerenciadores. A tarefa comum é abrir [comparacao.txt](./comparacao.txt), trocar `Resultado: aguardando` por `Resultado: concluído`, salvar como `resultado.txt` e reabrir esse arquivo.

## O que explicar em linguagem simples

- **Store:** local onde o Nix guarda componentes, normalmente `/nix/store`.
- **Perfil:** seleção de programas que aponta para os componentes guardados.
- **Geração:** registro de uma seleção anterior de um perfil.
- **Ambiente de projeto:** ferramentas disponibilizadas para trabalhar naquele projeto, a partir de uma configuração.
- **Configuração fixa:** arquivos que informam quais receitas utilizar, permitindo que outro integrante tente repetir o ambiente.

Relação com SO: o store mostra a organização de arquivos; os perfis mostram como selecionar executáveis; as gerações mostram como recuperar a seleção anterior. O arquivo de texto serve para demonstrar que recuperar programas e recuperar documentos são operações diferentes.

Fontes: [perfis e gerações](https://nix.dev/manual/nix/2.34/package-management/profiles.html), [ambientes declarativos](https://nix.dev/tutorials/first-steps/declarative-shell.html) e [fixação de dependências](https://nix.dev/tutorials/first-steps/towards-reproducibility-pinning-nixpkgs).

## Preparação antes da aula

- Usar Linux com Nix disponível. A configuração declara `x86_64-linux` e `aarch64-linux`; somente a primeira arquitetura foi validada nesta preparação.
- Para a tarefa com janela, usar uma sessão gráfica funcionando. Esta preparação ocorreu sem sessão gráfica; abrir e salvar pela janela continua pendente.
- Abrir um terminal **nesta pasta**, onde estão `flake.nix` e `flake.lock`.
- Manter os dois arquivos juntos. A revisão usada foi fixada explicitamente no `flake.nix`; não acompanha automaticamente uma branch nem atualiza sozinha.
- Ensaiar downloads e abertura antes da aula. Em Linux fora do NixOS, verificar a integração gráfica na máquina que será utilizada.

Os comandos abaixo foram conferidos com **Nix 2.34.9** e usam a interface de flakes, identificada como experimental pelo manual. Se o Nix pedir a habilitação, inserir `--extra-experimental-features 'nix-command flakes'` logo após `nix` em cada comando. Isso vale apenas para aquela execução e dispensa alterar a configuração global.

Exemplo:

```bash
nix --extra-experimental-features 'nix-command flakes' develop --no-update-lock-file
```

### 1. Conferir versão e caminho do editor

```bash
nix --version
nix eval --raw .#editor.version --no-update-lock-file
nix develop --no-update-lock-file --command gnome-text-editor --version
nix develop --no-update-lock-file --command sh -c 'command -v gnome-text-editor'
```

Explicar: a configuração fornece o editor e suas dependências; o caminho permite identificar qual executável está selecionado. `--no-update-lock-file` impede uma alteração não planejada do lock.

### 2. Executar a tarefa comum pela janela — pendente de validação

```bash
nix develop --no-update-lock-file --command gnome-text-editor --standalone comparacao.txt
```

Na janela, alterar a última linha e usar **Salvar como** para criar `resultado.txt` nesta pasta. Fechar e reabrir o resultado:

```bash
nix develop --no-update-lock-file --command gnome-text-editor --standalone resultado.txt
```

`--standalone` pede uma instância independente, evitando reaproveitar uma instância do editor já aberta por outra instalação. A opção existe na versão preparada; seu uso com janela ainda precisa ser ensaiado. Guardar uma captura com o resultado e outra com a versão.

### 3. Criar dois perfis de demonstração

Execute os blocos seguintes **no mesmo terminal** para preservar a variável com o diretório temporário:

```bash
nix_demo_dir=$(mktemp -d -t so-nix-aula-XXXXXXXX)
nix profile add --profile "$nix_demo_dir/perfil-a" .#editor --no-update-lock-file
nix profile add --profile "$nix_demo_dir/perfil-b" .#editor --no-update-lock-file
"$nix_demo_dir/perfil-a/bin/gnome-text-editor" --version
"$nix_demo_dir/perfil-b/bin/gnome-text-editor" --version
readlink -f "$nix_demo_dir/perfil-a/bin/gnome-text-editor"
readlink -f "$nix_demo_dir/perfil-b/bin/gnome-text-editor"
```

Os dois perfis selecionam **a mesma versão e o mesmo executável**. Isso demonstra seleção independente e compartilhamento do componente. Não demonstra coexistência de duas versões diferentes.

O argumento `--profile` direciona as operações a perfis temporários do exemplo. Na versão testada, `nix profile install` também é um alias de `nix profile add`. [Fonte: adicionar um pacote](https://nix.dev/manual/nix/2.34/command-ref/new-cli/nix3-profile-add.html).

### 4. Alterar apenas A e verificar B

```bash
nix profile remove --profile "$nix_demo_dir/perfil-a" --all
test ! -e "$nix_demo_dir/perfil-a/bin/gnome-text-editor" && echo 'Editor ausente de A'
"$nix_demo_dir/perfil-b/bin/gnome-text-editor" --version
nix profile history --profile "$nix_demo_dir/perfil-a"
```

Explicar: o editor saiu da seleção de A, enquanto B continua selecionando o componente. Usamos o caminho completo para evitar encontrar outra instalação pelo `PATH`. Remover de um perfil não significa apagar imediatamente o componente do store. [Fontes: remoção](https://nix.dev/manual/nix/2.34/command-ref/new-cli/nix3-profile-remove.html) e [coleta de lixo](https://nix.dev/manual/nix/2.34/package-management/garbage-collection.html).

### 5. Recuperar a seleção de A

```bash
nix profile rollback --profile "$nix_demo_dir/perfil-a"
"$nix_demo_dir/perfil-a/bin/gnome-text-editor" --version
```

Se a etapa gráfica foi concluída, observar o arquivo após o retorno:

```bash
cat resultado.txt
```

O programa volta à seleção de A. O texto continua com `Resultado: concluído`: o rollback do perfil não desfaz a edição do documento. Essa sequência demonstra recuperação após **remoção do perfil**, e não recuperação de uma atualização defeituosa. [Fonte: rollback](https://nix.dev/manual/nix/2.34/command-ref/new-cli/nix3-profile-rollback.html).

### 6. Repetição por outro integrante — pendente

Compartilhar esta pasta com `flake.nix`, `flake.lock` e `comparacao.txt`. Em outra máquina Linux compatível, o colega deve registrar seu SO, arquitetura e versão do Nix; executar os passos 1 e 2; anotar versão obtida, ajustes necessários e se conseguiu editar e reabrir o resultado. Não atualizar o lock durante essa verificação.

Já foi possível repetir a obtenção do editor em outra pasta **da mesma máquina**, conforme as evidências. Isso não substitui a repetição por um colega em outro computador.

## Limites que devem aparecer na apresentação

- O Nix mantém componentes e permite selecionar ambientes; isso não confina automaticamente o editor para impedir acesso aos documentos.
- O rollback demonstrado afeta um perfil, não todo o SO e os dados do usuário.
- Dois perfis com a mesma seleção não são um teste de duas versões.
- Não houve benchmark de tempo, RAM ou CPU. A quantidade baixada nesta máquina dependeu das dependências já presentes.
- A revisão deste exemplo é um registro fixo para a atividade. Mantê-la fixa não dispensa planejar e validar atualizações futuras.

## Roteiro de fala — cerca de 3 minutos, mais a demonstração

**Abertura:** “Minha parte mostra como o Nix organiza os programas. A ideia é guardar componentes em caminhos próprios e escolher quais vamos usar em cada ambiente.”

**Arquivos e dependências:** “O store é o local de armazenamento. O perfil funciona como uma seleção que aponta para esses componentes. Assim, podemos preparar seleções diferentes sem substituir diretamente todos os arquivos anteriores.”

**Exemplo:** “Usamos o mesmo editor do restante do grupo. Nesta demonstração, A e B selecionam a mesma versão. Quando retiramos o editor de A, ele continua disponível em B. Isso mostra que mudar uma seleção não exige mudar a outra.”

**Recuperação:** “Uma geração guarda uma seleção anterior. Ao voltar, recuperamos o editor em A. O documento continua alterado, porque voltar os programas não significa voltar os dados.”

**Equipe e limites:** “Os arquivos de configuração e a revisão fixa ajudam um colega a repetir o ambiente. Ainda precisamos considerar o sistema e a arquitetura usados. O custo inclui aprender a configuração e administrar o espaço ocupado por componentes preservados. Essa organização também não é uma barreira de acesso aos arquivos.”

Ao apresentar resultados, consultar a validação: a janela, a repetição em outra máquina e duas versões diferentes ainda não foram demonstradas nesta preparação.

## Conteúdo sugerido para três slides

**Slide 1 — Como o Nix organiza o software**

- Componentes em caminhos próprios.
- Perfis selecionam os programas.
- Projetos podem declarar ferramentas diferentes.

**Slide 2 — O que o exemplo mostra**

- Mesmo editor em dois perfis.
- Alterar A preserva a seleção de B.
- Uma geração permite recuperar A.

**Slide 3 — Benefícios e limites**

- Configuração compartilhada facilita repetir o ambiente.
- Recuperar programas não recupera documentos.
- Aprendizado e espaço em disco precisam ser considerados.

Usar os fundos e logos existentes quando esses tópicos forem incorporados à apresentação do grupo. A evidência e as fontes cabem nas notas; o slide deve manter o texto curto.
