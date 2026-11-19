# Plano de demonstrações e testes

**Estado atual:** os exemplos estão definidos. Debian e Ports foram incorporados a partir dos PDFs dos integrantes, sem evidência suficiente de execução. Nix tem validação inicial pelo terminal. Flatpak e Snap têm checagem documental e roteiro preparados, com execução pendente. Atualizar os estados somente após verificar cada procedimento.

O objetivo da semana 2 é selecionar e validar exemplos pequenos para a apresentação da semana 3. As ferramentas escolhidas precisam mostrar diferenças de organização e proteção; não precisam executar a mesma tarefa em um ranking de velocidade.

## 1. Debian — arquivos e dependências

- **Pergunta:** como identificar os arquivos e componentes de um pacote instalado?
- **Conceitos:** sistema de arquivos, metadados e dependências.
- **Ambiente e versão:** registrar versão do Debian, arquitetura e versões de APT/dpkg no piloto.
- **Pacote escolhido:** `tmux`, conforme o [material do integrante 1](./materiais-integrantes/debian-apt-dpkg.pdf).
- **Procedimento planejado:** instalar o pacote; consultar dependências com `apt-cache depends tmux`, arquivos com `dpkg -L tmux` e estado/versão com `dpkg -l tmux`; explicar algumas linhas de cada saída.
- **Evidência esperada:** comandos e saídas reais, ambiente e captura comentada. Seleção de versão e pinning devem ser explicados sem apresentar isso como isolamento por projeto.
- **Estado:** exemplo definido, execução ainda não comprovada pelo material recebido.
- **Resultado do piloto:** pendente de registro; os campos de status no PDF não estavam preenchidos.

## 2. FreeBSD Ports — construção

- **Pergunta:** quais etapas adicionais existem ao construir o software a partir das fontes?
- **Conceitos:** processos, CPU, memória e arquivos temporários.
- **Ambiente e versão:** registrar versão do FreeBSD, arquitetura, recursos da VM e revisão da árvore de Ports no piloto.
- **Port escolhido:** `misc/hello`, conforme o [material do integrante 2](./materiais-integrantes/freebsd-ports.pdf).
- **Procedimento planejado:** identificar a receita; verificar a opção NLS (suporte a idiomas) na revisão utilizada; registrar sua escolha; acompanhar configuração, compilação, geração do pacote e instalação; executar `hello`.
- **Evidência esperada:** opção efetivamente selecionada, trecho do log de construção, execução final e explicação do trabalho realizado. Se houver medidas, registrar caches, dependências e as etapas incluídas.
- **Estado:** exemplo definido, construção ainda não comprovada pelo material recebido.
- **Resultado do piloto:** pendente; não foram anexados logs, ambiente ou medidas.

FreeBSD exige ambiente próprio, como uma VM. Se ele não estiver disponível, registrar a pendência e preparar um exemplo documental com fonte explícita, sem apresentá-lo como execução do grupo.

## 3. Nix — perfis e variantes

- **Pergunta:** como selecionar um ambiente e manter variantes sem substituir diretamente os resultados anteriores?
- **Conceitos:** organização de arquivos, coexistência e recuperação.
- **Ambiente e versão:** NixOS `26.11.20261023.3ec6363`, `x86_64-linux`, Nix `2.34.9`; Nixpkgs na revisão `3ec636362e1816bc2f0888fa0fa2c69f1bc9e504`, fixada em `nix/flake.nix` e `nix/flake.lock`.
- **Exemplo escolhido:** GNOME Text Editor `50.1`, em ambiente declarado e dois perfis com a mesma versão.
- **Procedimento:** localizar executável e dependências; selecionar o editor em A e B; remover de A, verificar B e retornar à geração anterior de A; conferir o alcance da recuperação sobre um documento externo ao perfil.
- **Evidência:** [comandos, resultados e limites do piloto](./nix/evidencias/validacao.md).
- **Estado:** validado pelo terminal; edição pela janela e repetição em outra máquina pendentes.
- **Resultado do piloto:** A e B selecionaram o mesmo executável; remover de A preservou B; o rollback recuperou o editor em A. Um documento alterado pelo validador Python permaneceu alterado. Não houve teste de duas versões diferentes nem de atualização. Uma cópia da configuração em outra pasta da mesma máquina selecionou o mesmo pacote.

O [guia do integrante 3](./nix/README.md) fornece o procedimento para o grupo repetir o exemplo e completar a etapa gráfica.

## 4. Flatpak e Snap — acesso a recursos

- **Pergunta:** quais acessos a aplicação recebe e de quais configurações eles dependem?
- **Conceitos:** proteção, privilégios e recursos do processo.
- **Ambientes e versões:** execução pendente em Linux com ferramentas disponíveis, sessão gráfica e suporte de confinamento registrado. O ambiente de preparação não possui `flatpak`, `snap`, `snapcraft` ou `flatpak-builder` no PATH.
- **Aplicação:** GNOME Text Editor — Flatpak `org.gnome.TextEditor` e Snap `gnome-text-editor`; permite repetir a tarefa comum de abrir, editar, salvar e reabrir um documento.
- **Procedimento planejado:** consultar permissões e overrides no Flatpak e interfaces/modo/suporte de confinamento no Snap; executar a tarefa gráfica; observar acesso direto a arquivos antes e depois de uma mudança controlada de permissão; distinguir mediação por portais.
- **Evidência esperada:** versões e componentes instalados, permissões iniciais/finais, comandos e saídas reais, captura do resultado gráfico e interpretação dos limites.
- **Estado do Flatpak:** fundamentação e roteiro preparados; instalação, construção de pacote e execução pendentes.
- **Estado do Snap:** fundamentação e roteiro preparados; instalação, construção de pacote e execução pendentes.
- **Checagem documental realizada:** receita Flatpak fixada na revisão `5f9138c4ef35c63c58e54a5558f5661d249412a0`, com runtime 51, fonte do editor 51.0 e `--filesystem=host`; API da Snap Store em `latest/stable`/amd64 registrou versão 48.3, revisão 53, base core24 e metadado strict. Isso não comprova versão instalada, interfaces conectadas ou confinamento efetivo local.
- **Resultado dos pilotos:** ainda não executados. [Registro da checagem](./flatpak-snap/evidencias/validacao.md) e [guia do integrante 4](./flatpak-snap/README.md).

Se só uma ferramenta estiver disponível, usar a outra na comparação documental e declarar essa diferença.

## 5. Registro das evidências

Para cada piloto, guardar:

1. Data, responsável e ambiente utilizado.
2. Versões da ferramenta, aplicação e referências relevantes.
3. Procedimento ou comando realmente executado.
4. Saída ou captura de tela e uma frase explicando o que ela demonstra.
5. Limitações e ajustes necessários para repetir o exemplo.

Quando houver evidências reais, criar uma pasta `evidencias/` ao lado deste arquivo. Usar nomes descritivos, como `debian-arquivos.txt` ou `flatpak-permissoes.png`; não criar saídas simuladas para preencher a pasta.

## 6. Medidas opcionais nesta etapa

Os programas `tmux` e `hello` são pilotos didáticos dos mecanismos. A tarefa comum proposta com GNOME Text Editor precisa ser validada em cada ambiente, especialmente no FreeBSD. Se ela não for viável, definir exemplos comuns por comparação e registrar a mudança antes de coletar medidas. Os tempos e tamanhos de programas diferentes não sustentam um ranking direto de gerenciadores.

Se um piloto incluir tempo ou disco, registrar estado inicial, dependências presentes, caches e uso de rede. Repetir a operação sob condições equivalentes e guardar os valores individuais. Uma instalação já concluída não representa uma instalação nova.

Separar compilação, extração de arquivos e ativação de ambiente. A interpretação deve descrever o que foi feito e suas condições, sem extrapolar para um vencedor universal.
