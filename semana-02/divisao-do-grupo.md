# Divisão do trabalho entre os quatro integrantes

## Integrante 1 — Debian: APT/dpkg

**Realizar:** pesquisar a instalação de ferramentas e bibliotecas, preparar um exemplo pequeno e registrar os passos necessários para começar a trabalhar.

**Responder:**

- Qual é a função do APT e qual é a do dpkg?
- Como instalar e consultar as dependências necessárias?
- Como lidar com projetos que precisam de versões diferentes?
- O que uma atualização pode alterar no ambiente?
- Em quais situações essa opção é prática para o desenvolvedor e quais são suas limitações?

## Integrante 2 — FreeBSD Ports

**Realizar:** explicar as receitas de construção, acompanhar a compilação de um port pequeno e observar uma opção de configuração relevante.

**Responder:**

- Quais etapas existem entre obter o código-fonte e instalar o programa?
- O que o desenvolvedor consegue personalizar?
- Qual é o custo dessa construção em tempo, CPU, memória e disco?
- Como outra pessoa repetiria a construção com as mesmas opções?
- Quando esse controle adicional compensa o esforço de preparação e manutenção?

## Integrante 3 — Nix

**Realizar:** preparar um exemplo de ambiente com ferramentas e dependências definidas, observar variantes ou perfis e verificar como outra pessoa poderia reutilizar a configuração.

**Responder:**

- Como o Nix organiza versões e dependências?
- Como manter ambientes diferentes para projetos diferentes?
- O que precisa ser registrado para repetir o ambiente em outra máquina?
- O que pode ser recuperado ao retornar a uma geração anterior?
- Quais benefícios e dificuldades aparecem para quem desenvolve individualmente ou em equipe?

## Integrante 4 — Flatpak e Snap

**Realizar:** comparar as duas ferramentas separadamente, estudar o empacotamento de uma aplicação e examinar suas dependências e permissões. Identificar claramente quais procedimentos foram testados e quais foram apenas pesquisados.

**Responder:**

- Como transformar uma aplicação em um pacote instalável?
- Como cada ferramenta fornece as dependências necessárias?
- Qual é a função de OSTree/Bubblewrap e de SquashFS/AppArmor/cgroups?
- Como as permissões afetam arquivos, rede e outros recursos usados pela aplicação?
- Qual é o esforço para distribuir, atualizar e manter a aplicação em cada alternativa?

## Entrega comum

Cada integrante deve entregar:

- Uma seção para o relatório.
- Fontes oficiais utilizadas.
- Um exemplo explicado.
- Uma síntese das vantagens, limitações e situações de uso.

Na conclusão conjunta, comparar as respostas e indicar **qual opção faz mais sentido para cada necessidade**, justificando a escolha com o que foi pesquisado ou observado.
