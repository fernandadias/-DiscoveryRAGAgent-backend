# Diretrizes de Produto

Este documento define as diretrizes estratégicas e metodológicas que guiam as decisões de produto do time responsável pelo Software Horizontal voltado a clientes Micro e Small, com foco especial na iniciativa de personalização da Home do aplicativo. O objetivo é garantir consistência, alinhamento e assertividade nas respostas de agentes com acesso a esse material via RAG/LLM.

## Motivação e Objetivos da Discovery

A Home atual do aplicativo apresenta uma experiência genérica que não reflete a diversidade de perfis dos clientes da Stone, desde o microempreendedor até a PME com estrutura de gestão. Essa abordagem "one-size-fits-all" tem gerado:

- Subutilização de funcionalidades
- Dificuldade em encontrar informações relevantes
- Baixa percepção de valor
- Experiência fragmentada

A personalização da Home é vista como um motor estratégico para:

- Aumentar o engajamento e frequência de uso
- Melhorar a retenção e o LTV
- Reforçar o papel da Stone como parceira na operação e gestão do negócio
- Evidenciar o ecossistema de soluções de forma contextual

Expectativa da Discovery: gerar uma base clara de hipóteses e evidências que oriente a construção de uma Home personalizada, relevante e eficiente. Os outputs esperados incluem:

- Mapeamento de perfis e hábitos operacionais dos usuários
- Definição dos principais módulos e informações contextuais
- Identificação de oportunidades para descoberta e educação
- Direcionamento claro para o MVP da personalização

## Visão e Princípios

**Visão**: Ajudar pequenos empreendedores a venderem mais e gerirem melhor seus negócios. A Home deve funcionar como um painel de controle inteligente e adaptável, maximizando a utilidade da plataforma e fortalecendo o vínculo com o cliente.

**Princípios**:

- Resolver dores reais com foco em contexto e momento do cliente
- Promover simplicidade e eficiência (menos cliques, mais impacto)
- Aumentar o engajamento com o ecossistema Stone de forma contextual
- Fomentar descoberta e educação contínua a partir da interface

## Metodologia de Discovery

Baseada na "Esteira de Produto", nossa abordagem segue cinco etapas:

1. **Oportunidade**
   - Consolidar dados de mercado, jornadas e comportamento
   - Formular problem statements conectados a objetivos estratégicos

2. **Visão & Estratégia**
   - Definir visão de personalização com pilares (eficiência, relevância, descoberta)
   - Planejar roadmap faseado e alinhamento organizacional

3. **Go to Market**
   - Construir MVP com reordenação de atalhos e módulo financeiro personalizado
   - Validar uso, adoção e feedback qualitativo

4. **Product Market Fit**
   - Avaliar aderência com cohort de usuários e insights comportamentais
   - Refatorar com base em NPS, CSAT e métricas de conversão

5. **Escala & Otimização**
   - Implementar personalização preditiva com IA
   - Sustentar crescimento com eficiência técnica e evoluções contínuas

## Critérios de Priorização

- Potencial de aumentar engajamento com funcionalidades-chave
- Impacto direto em churn, LTV e percepção de valor
- Aderência à visão de produto inteligente e adaptável
- Viabilidade técnica e sinergia com componentes existentes
- Alavancas de diferenciação no mercado financeiro/empreendedor

## Métricas de Sucesso

- **Adoção**: uso de atalhos e módulos personalizados na Home
- **Engajamento**: aumento de DAU, tempo médio e funcionalidades ativadas
- **Conversão**: crescimento na adoção a partir de interações iniciadas pela Home
- **Retenção**: redução de churn e aumento de tempo de vida da conta
- **Satisfação**: aumento em NPS e CSAT entre usuários da Home personalizada

## Valores e Trade-offs

**Valores priorizados**:

- Clareza > Complexidade
- Utilidade prática > Beleza estética
- Contextualização > Generalização
- Descoberta ativa > Passividade de interface

**Trade-offs aceitáveis**:

- Reduzir opções manuais em prol de sugestões inteligentes
- Favorecer desempenho e estabilidade a uma hiperconfiguração

## Linguagem e Terminologia

- **Home personalizada**: tela inicial dinâmica e adaptável
- **Atalhos**: acessos diretos reordenáveis na Home
- **Módulos**: blocos informacionais (ex: saldo, vendas, recebimentos)
- **MVP**: versão mínima para validação de valor
- **Personalização proativa**: sugestões baseadas em comportamento e perfil
- **Heavy user**: cliente com uso intenso e contínuo
- **DAU/MAU**: métricas de uso diário/mensal
- **ROI**: retorno sobre investimento em funcionalidades ou jornadas

## Exemplos de Personalização por Perfil

**Microempreendedor Individual (MEI)**:
- Destaque para saldo e vendas do dia
- Atalhos para Pix e transferências
- Módulo simplificado de gestão financeira
- Conteúdo educativo sobre formalização e crescimento
- Notificações sobre datas importantes (impostos, declarações)

**Pequeno Comércio Varejista**:
- Dashboard de vendas com comparativos semanais
- Atalhos para gestão de estoque e conciliação
- Módulo de fluxo de caixa com previsibilidade
- Insights sobre sazonalidade e tendências de vendas
- Sugestões de produtos financeiros adequados ao ciclo de negócio

**Prestador de Serviços**:
- Visão de agenda e compromissos financeiros
- Atalhos para emissão de notas fiscais e cobranças
- Módulo de gestão de clientes e recorrência
- Alertas de oportunidades baseados em histórico de serviços
- Ferramentas de precificação e controle de horas

## Desafios e Limitações Conhecidas

**Desafios Técnicos**:
- Integração com múltiplas fontes de dados em tempo real
- Latência na personalização dinâmica em conexões instáveis
- Balanceamento entre dados armazenados localmente e em nuvem
- Compatibilidade com diferentes versões do aplicativo em uso

**Limitações de Personalização**:
- Necessidade de período inicial de aprendizado sobre o usuário
- Equilíbrio entre automação e controle manual das preferências
- Risco de criar "bolhas" que limitem a descoberta de novas funcionalidades
- Complexidade de atender múltiplos perfis em uma mesma conta

**Considerações Éticas**:
- Transparência sobre dados utilizados para personalização
- Respeito à privacidade e conformidade com LGPD
- Evitar vieses algorítmicos que possam prejudicar determinados perfis
- Garantir acessibilidade para todos os usuários independente da personalização

## Incorporação de Feedback e Iterações

**Mecanismos de Feedback**:
- Pesquisas in-app após interações significativas
- Análise de comportamento e padrões de uso (heatmaps, jornadas)
- Entrevistas qualitativas com usuários de diferentes perfis
- Monitoramento contínuo de métricas de engajamento e satisfação
- Canal direto para sugestões e relatos de problemas

**Ciclo de Iteração**:
1. **Coleta**: Agregação de feedback quantitativo e qualitativo
2. **Análise**: Identificação de padrões e priorização de insights
3. **Hipótese**: Formulação de melhorias baseadas em evidências
4. **Teste**: Implementação em grupos controlados (A/B testing)
5. **Aprendizado**: Documentação de resultados e decisões
6. **Escala**: Implementação ampla das melhorias validadas

**Governança de Produto**:
- Revisões quinzenais de métricas e feedback
- Atualização mensal de prioridades baseada em aprendizados
- Documentação transparente de decisões e trade-offs
- Envolvimento contínuo de stakeholders de diferentes áreas
- Alinhamento trimestral com roadmap estratégico da empresa
