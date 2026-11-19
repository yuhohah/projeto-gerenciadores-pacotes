# Escopo e plano do projeto

## Objetivo

Explicar como diferentes estratégias de gerenciamento de pacotes organizam o software e afetam arquivos, compatibilidade, recuperação e proteção em Unix/Linux. O trabalho prioriza comparações acessíveis e exemplos relacionados aos conceitos de Sistemas Operacionais.

## Representantes

- **Binários tradicionais mutáveis (FHS):** apenas Debian, com APT/dpkg.
- **Baseados em código-fonte (Source/Ports):** apenas FreeBSD Ports.
- **Funcionais e imutáveis:** apenas Nix.
- **Containerizados / sandboxed:** Flatpak (OSTree + Bubblewrap) e Snap (SquashFS + AppArmor/cgroups).

APT e dpkg são camadas complementares do representante Debian. FreeBSD Ports representa a construção a partir de fontes; não é o gerenciador de pacotes binários do FreeBSD.

## Critérios comuns

1. **Arquivos:** onde ficam e como são registrados.
2. **Dependências:** compatibilidade e coexistência de versões.
3. **Atualizações:** quais mudanças podem ser recuperadas e quais dados permanecem.
4. **Proteção:** acesso a arquivos, dispositivos e outros recursos.
5. **Recursos:** custo inicial, componentes reaproveitados e condições da comparação.

## Exemplos planejados

- Debian: consultar arquivos e dependências de um pacote.
- FreeBSD Ports: acompanhar a construção de um port pequeno em ambiente próprio.
- Nix: observar variantes e seleção de perfis.
- Flatpak/Snap: examinar e comparar acesso a recursos.

A configuração e a execução desses exemplos ainda precisam ser validadas. FreeBSD requer um ambiente próprio, como uma máquina virtual; não compartilha o kernel de um container Linux comum.

Tempo e espaço em disco podem apoiar a análise. Registrar versões, funcionalidades dos pacotes, dependências novas, caches e condições de rede. Compilação, instalação de binários e ativação de perfis são operações distintas, portanto seus tempos não devem compor um ranking direto de velocidade.

## Entregas previstas

- **Semana 1:** apresentação oral da proposta, com tema, escopo e objetivos.
- **Semana 2:** relatório parcial 1 e slides, com revisão e plano de testes.
- **Semana 3:** apresentação oral 2, com demonstrações das quatro famílias.
- **Semana 4:** relatório parcial 2 e slides, com comparação e medidas.
- **Semana 5:** relatório final e slides, com resultados, limites e conclusões.

A primeira apresentação está preparada em [slides/](./slides/README.md). Sua realização e a aprovação pelo professor não estão registradas nesta pasta. Não há resultados experimentais coletados no material atual.

## Apresentação oral

O grupo tem quatro integrantes. As falas e os tempos sugeridos estão no [roteiro atual](./slides/roteiro-de-fala.md), que acompanha os 11 slides. A duração estimada é de oito minutos, a confirmar em ensaio.
