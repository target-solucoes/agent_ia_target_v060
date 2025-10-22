"""
Numeric Analyzer - Camada de Análise Numérica para Insights Inteligentes

Este módulo implementa a camada simbólica da arquitetura híbrida,
extraindo métricas derivadas e padrões dos dados ANTES de chamar a LLM.
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, List, Tuple


def gerar_resumo_numerico(df: pd.DataFrame, eixo_x: str, eixo_y: str, tipo_grafico: str, total_universo: float = None) -> Dict[str, Any]:
    """
    Gera resumo numérico estruturado com métricas derivadas.

    Esta função analisa o DataFrame e extrai estatísticas relevantes
    que servirão como base analítica para a LLM gerar insights.

    Args:
        df: DataFrame com os dados do gráfico
        eixo_x: Nome da coluna do eixo X (labels/categorias)
        eixo_y: Nome da coluna do eixo Y (valores numéricos)
        tipo_grafico: Tipo do gráfico ("horizontal_bar", "vertical_bar", "stacked_bar", "line")
        total_universo: Total do universo completo filtrado (para cálculos de concentração corretos)

    Returns:
        Dicionário com métricas estruturadas

    Example:
        >>> df = pd.DataFrame({'categoria': ['A', 'B', 'C'], 'vendas': [100, 70, 40]})
        >>> resumo = gerar_resumo_numerico(df, 'categoria', 'vendas', 'horizontal_bar', total_universo=500)
        >>> resumo['concentracao_top3_pct']
        42.0
    """
    resumo = {
        "tipo_grafico": tipo_grafico,
        "num_categorias": len(df),
        "total_geral": float(df[eixo_y].sum()),
        "media": float(df[eixo_y].mean()),
        "mediana": float(df[eixo_y].median())
    }

    # Métricas específicas por tipo de gráfico
    if tipo_grafico == "horizontal_bar":
        resumo.update(_analisar_ranking(df, eixo_x, eixo_y, total_universo=total_universo))

    elif tipo_grafico == "vertical_bar":
        resumo.update(_analisar_comparacao(df, eixo_x, eixo_y))

    elif tipo_grafico in ["grouped_vertical_bar", "stacked_bar"]:
        resumo.update(_analisar_comparacao_agrupada(df, eixo_x, eixo_y))

    elif tipo_grafico == "line":
        resumo.update(_analisar_temporal(df, eixo_x, eixo_y))

    return resumo


def _analisar_ranking(df: pd.DataFrame, label_col: str, value_col: str, total_universo: float = None) -> Dict[str, Any]:
    """
    Analisa dados de ranking (horizontal bar charts).

    Métricas calculadas:
    - Top N categorias
    - Concentração (top 3, top 5) - CORRIGIDO para usar total do universo filtrado
    - Gaps entre posições
    - Desvios da média

    Args:
        df: DataFrame com os dados do ranking (pode ser apenas Top N)
        label_col: Nome da coluna de labels
        value_col: Nome da coluna de valores
        total_universo: Total do universo completo filtrado (para cálculo correto de concentração)
    """
    df_sorted = df.sort_values(value_col, ascending=False).reset_index(drop=True)
    
    # CORREÇÃO CRÍTICA: Usar total_universo se disponível, senão usar total do df (comportamento legado)
    # O total_universo representa a soma de TODOS os elementos com os filtros ativos,
    # não apenas a soma do Top N
    total = total_universo if total_universo is not None else df_sorted[value_col].sum()
    total_topn = df_sorted[value_col].sum()

    metricas = {
        "top_categorias": df_sorted[label_col].head(3).tolist(),
        "valor_max": float(df_sorted[value_col].iloc[0]),
        "valor_min": float(df_sorted[value_col].iloc[-1]),
        "categoria_max": str(df_sorted[label_col].iloc[0]),
        "categoria_min": str(df_sorted[label_col].iloc[-1]),
        "total_topn": float(total_topn),  # Soma do Top N
        "total_universo": float(total)    # Soma do universo completo
    }

    # Concentração CORRIGIDA - agora calcula sobre o universo completo
    if len(df_sorted) >= 3:
        top3_sum = df_sorted[value_col].head(3).sum()
        metricas["concentracao_top3_pct"] = round((top3_sum / total) * 100, 1)

    if len(df_sorted) >= 5:
        top5_sum = df_sorted[value_col].head(5).sum()
        metricas["concentracao_top5_pct"] = round((top5_sum / total) * 100, 1)

    # Gaps entre posições
    if len(df_sorted) >= 2:
        gap_1_2 = df_sorted[value_col].iloc[0] - df_sorted[value_col].iloc[1]
        metricas["gap_1_2"] = float(gap_1_2)
        metricas["gap_1_2_pct"] = round((gap_1_2 / df_sorted[value_col].iloc[1]) * 100, 1)

    # Diferença max-min
    diferenca = metricas["valor_max"] - metricas["valor_min"]
    metricas["diferenca_max_min"] = float(diferenca)
    metricas["amplitude_relativa"] = round((diferenca / metricas["valor_min"]) * 100, 1) if metricas["valor_min"] > 0 else None

    # Desvio do líder em relação à média
    media = df_sorted[value_col].mean()
    desvio_lider = metricas["valor_max"] - media
    metricas["desvio_lider_media_pct"] = round((desvio_lider / media) * 100, 1)

    # Múltiplo do líder vs segundo
    if len(df_sorted) >= 2 and df_sorted[value_col].iloc[1] > 0:
        metricas["multiplo_1_vs_2"] = round(df_sorted[value_col].iloc[0] / df_sorted[value_col].iloc[1], 2)

    # Contribuição do líder ao total
    metricas["contribuicao_lider_pct"] = round((metricas["valor_max"] / total) * 100, 1)

    return metricas


def _analisar_comparacao(df: pd.DataFrame, label_col: str, value_col: str) -> Dict[str, Any]:
    """
    Analisa comparações diretas (vertical bar charts com 2-5 itens).

    Métricas calculadas:
    - Diferenças percentuais entre categorias
    - Categoria dominante
    - Variação relativa
    """
    df_sorted = df.sort_values(value_col, ascending=False).reset_index(drop=True)

    metricas = {
        "categoria_maior": str(df_sorted[label_col].iloc[0]),
        "categoria_menor": str(df_sorted[label_col].iloc[-1]),
        "valor_maior": float(df_sorted[value_col].iloc[0]),
        "valor_menor": float(df_sorted[value_col].iloc[-1])
    }

    # Diferença percentual
    if metricas["valor_menor"] > 0:
        diferenca_pct = ((metricas["valor_maior"] - metricas["valor_menor"]) / metricas["valor_menor"]) * 100
        metricas["diferenca_pct"] = round(diferenca_pct, 1)

    # Diferença de pontos percentuais (se houver total)
    total = df_sorted[value_col].sum()
    pct_maior = (metricas["valor_maior"] / total) * 100
    pct_menor = (metricas["valor_menor"] / total) * 100
    metricas["diferenca_pontos_percentuais"] = round(pct_maior - pct_menor, 1)

    # Contribuição ao total
    metricas["contribuicao_maior_pct"] = round(pct_maior, 1)
    metricas["contribuicao_menor_pct"] = round(pct_menor, 1)

    # Se houver 2 itens, calcular proporção
    if len(df_sorted) == 2:
        metricas["proporcao_relativa"] = f"{round(pct_maior, 0)}% vs {round(pct_menor, 0)}%"

    return metricas


def _analisar_comparacao_agrupada(df: pd.DataFrame, group_col: str, value_col: str) -> Dict[str, Any]:
    """
    Analisa comparações agrupadas (grouped vertical bar charts).

    Nota: Esta função recebe estrutura diferente - group + category + value
    Assumindo que df já foi processado e group_col contém os grupos.
    """
    # Fallback para análise de comparação simples
    # (a estrutura agrupada seria melhor analisada com acesso a 'category' também)
    return _analisar_comparacao(df, group_col, value_col)


def _analisar_temporal(df: pd.DataFrame, date_col: str, value_col: str) -> Dict[str, Any]:
    """
    Analisa séries temporais (line charts).

    Métricas calculadas:
    - Tendência (crescente/decrescente)
    - Taxa de crescimento
    - Picos e vales
    - Variação período a período
    """
    df_sorted = df.sort_values(date_col).reset_index(drop=True)

    metricas = {
        "num_periodos": len(df_sorted),
        "valor_inicial": float(df_sorted[value_col].iloc[0]),
        "valor_final": float(df_sorted[value_col].iloc[-1])
    }

    # Tendência
    if metricas["valor_final"] > metricas["valor_inicial"]:
        metricas["tendencia"] = "crescente"
    elif metricas["valor_final"] < metricas["valor_inicial"]:
        metricas["tendencia"] = "decrescente"
    else:
        metricas["tendencia"] = "estável"

    # Taxa de crescimento total
    if metricas["valor_inicial"] > 0:
        taxa_crescimento = ((metricas["valor_final"] - metricas["valor_inicial"]) / metricas["valor_inicial"]) * 100
        metricas["taxa_crescimento_pct"] = round(taxa_crescimento, 1)

    # Picos e vales
    idx_max = df_sorted[value_col].idxmax()
    idx_min = df_sorted[value_col].idxmin()

    metricas["pico_valor"] = float(df_sorted.loc[idx_max, value_col])
    metricas["pico_periodo"] = str(df_sorted.loc[idx_max, date_col])
    metricas["vale_valor"] = float(df_sorted.loc[idx_min, value_col])
    metricas["vale_periodo"] = str(df_sorted.loc[idx_min, date_col])

    # Amplitude (diferença entre pico e vale)
    metricas["amplitude"] = float(metricas["pico_valor"] - metricas["vale_valor"])
    if metricas["vale_valor"] > 0:
        metricas["amplitude_pct"] = round((metricas["amplitude"] / metricas["vale_valor"]) * 100, 1)

    # Variação média período a período
    if len(df_sorted) > 1:
        variacoes = df_sorted[value_col].pct_change().dropna()
        if len(variacoes) > 0:
            metricas["variacao_media_pct"] = round(variacoes.mean() * 100, 1)
            metricas["volatilidade"] = round(variacoes.std() * 100, 1)

    # Detectar aceleração (segundo semestre vs primeiro semestre)
    if len(df_sorted) >= 6:
        metade = len(df_sorted) // 2
        media_primeira_metade = df_sorted[value_col].iloc[:metade].mean()
        media_segunda_metade = df_sorted[value_col].iloc[metade:].mean()

        if media_primeira_metade > 0:
            aceleracao = ((media_segunda_metade - media_primeira_metade) / media_primeira_metade) * 100
            metricas["aceleracao_segunda_metade_pct"] = round(aceleracao, 1)

            if aceleracao > 10:
                metricas["comportamento_temporal"] = "aceleração no segundo período"
            elif aceleracao < -10:
                metricas["comportamento_temporal"] = "desaceleração no segundo período"
            else:
                metricas["comportamento_temporal"] = "ritmo constante"

    return metricas


def gerar_prompt_insights(resumo_numerico: Dict[str, Any], tipo_grafico: str, max_insights: int = 5) -> str:
    """
    Gera prompt estruturado para a LLM criar insights inteligentes.

    Este prompt será injetado no contexto do agente para guiar
    a geração de insights baseados no resumo numérico.

    Args:
        resumo_numerico: Dicionário com métricas calculadas
        tipo_grafico: Tipo do gráfico
        max_insights: Número máximo de insights desejados (padrão: 5)

    Returns:
        String formatada com prompt para LLM
    """
    import json

    # Formatar resumo de forma legível
    resumo_formatado = json.dumps(resumo_numerico, indent=2, ensure_ascii=False)

    # Template base do prompt
    prompt = f"""
🧮 RESUMO NUMÉRICO ESTRUTURADO DISPONÍVEL

Você recebeu um resumo analítico pré-calculado com métricas derivadas:

```json
{resumo_formatado}
```

## 🎯 TAREFA: Gerar {max_insights} Insights Não-Óbvios

Use o resumo numérico acima como BASE ANALÍTICA para gerar insights estratégicos.

### ✅ O QUE FAZER:
- Interpretar padrões e implicações (não apenas descrever números)
- Usar métricas derivadas (concentração, gaps, múltiplos, desvios)
- Focar em PROPORÇÕES e RELAÇÕES (não valores absolutos isolados)
- Identificar oportunidades ou riscos estratégicos
- Usar **negrito** para palavras-chave importantes

### ❌ O QUE NÃO FAZER:
- Repetir valores que estão visíveis no gráfico
- Listar dados sem interpretação ("A é maior que B")
- Usar frases genéricas ("distribuição desigual")
- Mencionar mais de {max_insights} insights

### 📋 ESTRUTURA OBRIGATÓRIA:
Cada insight deve ter este formato:
- **Título descritivo**: Interpretação com números contextualizados (%, múltiplos, pontos percentuais)

### 🎨 EXEMPLO DE TRANSFORMAÇÃO:
❌ ERRADO: "SC é o maior estado"
✅ CORRETO: "**Concentração significativa**: SC representa 43% do total, superando RS em +12 p.p."

---
"""

    # Adicionar diretrizes específicas por tipo de gráfico
    if tipo_grafico == "horizontal_bar":
        prompt += """
### 📊 FOCO PARA RANKINGS:
- Concentração (top N representa X% do total)
- Gap entre liderança e demais (líder é X vezes maior que segundo)
- Oportunidades em posições intermediárias ou cauda longa
- Dependência ou risco de concentração excessiva
"""

    elif tipo_grafico == "vertical_bar":
        prompt += """
### 📊 FOCO PARA COMPARAÇÕES:
- Diferença percentual e pontos percentuais entre categorias
- Proporções relativas (X contribui com Y% vs Z com W%)
- Identificar categoria dominante e margem de liderança
- Potencial de rebalanceamento ou crescimento
"""

    elif tipo_grafico == "line":
        prompt += """
### 📊 FOCO PARA SÉRIES TEMPORAIS:
- Tendência geral (crescente/decrescente/estável)
- Taxa de crescimento e aceleração
- Picos e vales (quando e por quê podem ter ocorrido)
- Sazonalidade ou padrões recorrentes
- Comparação primeira vs segunda metade do período
"""

    elif tipo_grafico in ["grouped_vertical_bar", "stacked_bar"]:
        prompt += """
### 📊 FOCO PARA COMPARAÇÕES AGRUPADAS:
- Diferenças entre grupos/períodos
- Categorias que cresceram/decresceram
- Mudanças estruturais no mix
- Liderança por grupo e shifts de posição
"""

    prompt += """
---

⚠️ IMPORTANTE:
- Use estas métricas para ENRIQUECER a seção de Insights da sua resposta
- NUNCA gere APENAS insights - SEMPRE inclua os 5 elementos obrigatórios:
  1. ## Título
  2. **Contexto:** (com filtros)
  3. [Gráfico automático]
  4. ### 💡 Principais Insights ({max_insights} itens baseados nas métricas acima)
  5. ### 🔍 Próximos Passos

O gráfico mostra OS DADOS. Você fornece OS INSIGHTS (dentro da estrutura completa).
""".format(max_insights=max_insights)

    return prompt


def formatar_metricas_para_exibicao(resumo: Dict[str, Any]) -> str:
    """
    Formata resumo numérico para exibição legível (útil para debug).

    Args:
        resumo: Dicionário com métricas

    Returns:
        String formatada para exibição
    """
    linhas = []
    linhas.append("Resumo Numerico:")
    linhas.append(f"  - Tipo: {resumo.get('tipo_grafico', 'N/A')}")
    linhas.append(f"  - Categorias: {resumo.get('num_categorias', 0)}")
    linhas.append(f"  - Total: {resumo.get('total_geral', 0):,.0f}")
    linhas.append(f"  - Media: {resumo.get('media', 0):,.0f}")

    if 'concentracao_top3_pct' in resumo:
        linhas.append(f"  - Concentracao Top 3: {resumo['concentracao_top3_pct']}%")

    if 'gap_1_2_pct' in resumo:
        linhas.append(f"  - Gap 1o vs 2o: {resumo['gap_1_2_pct']}%")

    if 'tendencia' in resumo:
        linhas.append(f"  - Tendencia: {resumo['tendencia']}")

    if 'taxa_crescimento_pct' in resumo:
        linhas.append(f"  - Crescimento: {resumo['taxa_crescimento_pct']:+.1f}%")

    return '\n'.join(linhas)
