"""
Funções de visualização com Plotly para gráficos de barras e linhas
"""

import streamlit as st
import plotly.express as px
import pandas as pd
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from utils.formatters import format_compact_number


def render_plotly_visualization(visualization_data):
    """
    Renderiza gráfico Plotly baseado nos dados de visualização do agente.
    Retorna True se renderizou um gráfico, False se renderizou uma tabela.
    """
    if not visualization_data:
        return False

    # Se não é para visualizar como gráfico, não fazer nada
    chart_type = visualization_data.get('type')
    if chart_type not in ['bar_chart', 'line_chart', 'vertical_bar_chart', 'grouped_vertical_bar_chart'] or not visualization_data.get('has_data', False):
        return False

    try:
        # Obter dados do DataFrame
        df = visualization_data.get('data')
        config = visualization_data.get('config', {})

        if df is None or df.empty:
            return False

        # Processar baseado no tipo de gráfico
        if chart_type == 'line_chart':
            # Lógica específica para gráficos de linha
            return render_line_chart(df, config)
        elif chart_type == 'vertical_bar_chart':
            # Lógica para gráficos de barras verticais (comparações)
            return render_vertical_bar_chart(df, config)
        elif chart_type == 'grouped_vertical_bar_chart':
            # Lógica para gráficos de barras verticais agrupadas (comparações com categorias)
            return render_grouped_vertical_bar_chart(df, config)
        else:
            # Lógica original para gráficos de barra horizontal (rankings)
            return render_bar_chart(df, config)

    except Exception as e:
        # Em caso de erro, não fazer nada e deixar o conteúdo textual aparecer
        st.error(f"Erro ao renderizar gráfico: {str(e)}")
        return False


def render_bar_chart(df, config):
    """
    Renderiza gráfico de barras horizontais
    """
    # Preparar rótulos compactos para as barras
    df_with_labels = df.copy()
    df_with_labels['value_label'] = df_with_labels['value'].apply(format_compact_number)

    # Verificar se foi detectado como ID categórico pelo backend e ajustar labels
    is_categorical_id = config.get('is_categorical_id', False)

    # Detecção adicional no frontend como fallback
    if not is_categorical_id and not df_with_labels.empty:
        sample_labels = df_with_labels['label'].head().astype(str)
        # Padrões que indicam IDs categóricos: números de 3-8 dígitos
        for label in sample_labels:
            if label.isdigit() and 3 <= len(label) <= 8:
                is_categorical_id = True
                break

    # Formatar labels para IDs categóricos
    if is_categorical_id:
        original_col = config.get('original_label_column', '')
        if 'cliente' in original_col.lower():
            # Para códigos de cliente, adicionar prefixo
            df_with_labels['label'] = 'Cliente ' + df_with_labels['label'].astype(str)

    # Criar gráfico de barras horizontais
    fig = px.bar(
        df_with_labels,
        x='value',
        y='label',
        orientation='h',
        title=config.get('title', 'Top Resultados'),
        labels={
            'value': 'Valor',
            'label': 'Item'
        },
        text='value_label'  # Usar rótulos compactos
    )

    # Configurações de layout para melhor aparência
    fig.update_layout(
        height=max(400, len(df) * 45),  # Altura ligeiramente aumentada para acomodar rótulos
        margin=dict(l=20, r=120, t=50, b=20),  # Margem direita aumentada para rótulos
        xaxis_title=config.get('original_value_column', 'Valor'),
        yaxis_title="",
        showlegend=False,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
    )

    # Personalizar barras com cores azuis harmoniosas
    fig.update_traces(
        marker_color='#3498db',  # Azul agradável e harmonioso
        marker_line_color='#2980b9',  # Borda azul mais escura
        marker_line_width=1.5,
        opacity=0.85,
        textposition='outside',  # Posição dos rótulos fora das barras
        textfont=dict(size=11, color='#2c3e50', family='Arial')  # Estilo do texto dos rótulos
    )

    # Configurações do eixo Y para melhor legibilidade
    if is_categorical_id:
        # Forçar tratamento como categoria para códigos de cliente/produto
        fig.update_yaxes(
            type='category',  # Forçar tipo categoria
            categoryorder='total ascending',  # Ordenar por valor
            tickfont=dict(size=12, family='Arial')
        )
    else:
        # Comportamento padrão para outras categorias
        fig.update_yaxes(
            categoryorder='total ascending',  # Ordenar por valor
            tickfont=dict(size=12, family='Arial')
        )

    # Configurações do eixo X com formatação inteligente e estilo aprimorado
    value_format = config.get('value_format', 'number')
    if value_format == 'currency':
        fig.update_xaxes(
            tickformat=',.0f',  # Formato monetário com separadores de milhares
            tickprefix='R$ ',
            tickfont=dict(size=10, family='Arial'),
            gridcolor='rgba(52, 152, 219, 0.2)',  # Grid sutil em azul
            gridwidth=1
        )
    else:
        fig.update_xaxes(
            tickformat=',.0f',  # Formato numérico com separadores de milhares
            tickfont=dict(size=10, family='Arial'),
            gridcolor='rgba(52, 152, 219, 0.2)',  # Grid sutil em azul
            gridwidth=1
        )

    # Ajustar título do gráfico com melhor estilo
    fig.update_layout(
        title_font=dict(size=16, family='Arial', color='#2c3e50'),
        title_x=0.5  # Centralizar título
    )

    # Renderizar o gráfico no Streamlit
    st.plotly_chart(fig, use_container_width=True, theme="streamlit")

    return True


def render_vertical_bar_chart(df, config):
    """
    Renderiza gráfico de barras verticais para comparações diretas.
    Ideal para comparar 2-5 categorias ou períodos específicos.
    """
    # Preparar rótulos compactos para as barras
    df_with_labels = df.copy()
    df_with_labels['value_label'] = df_with_labels['value'].apply(format_compact_number)

    # Verificar se foi detectado como ID categórico pelo backend
    is_categorical_id = config.get('is_categorical_id', False)

    # Detecção adicional no frontend como fallback
    if not is_categorical_id and not df_with_labels.empty:
        sample_labels = df_with_labels['label'].head().astype(str)
        # Padrões que indicam IDs categóricos: números de 3-8 dígitos
        for label in sample_labels:
            if label.isdigit() and 3 <= len(label) <= 8:
                is_categorical_id = True
                break

    # Formatar labels para IDs categóricos
    if is_categorical_id:
        original_col = config.get('original_label_column', '')
        if 'cliente' in original_col.lower():
            df_with_labels['label'] = 'Cliente ' + df_with_labels['label'].astype(str)
        elif 'produto' in original_col.lower():
            df_with_labels['label'] = 'Produto ' + df_with_labels['label'].astype(str)

    # Criar gráfico de barras verticais
    fig = px.bar(
        df_with_labels,
        x='label',
        y='value',
        orientation='v',  # Orientação vertical
        title=config.get('title', 'Comparação de Valores'),
        labels={
            'value': 'Valor',
            'label': 'Categoria'
        },
        text='value_label'  # Usar rótulos compactos
    )

    # Configurações de layout para melhor aparência
    fig.update_layout(
        height=500,  # Altura fixa adequada para barras verticais
        margin=dict(l=50, r=50, t=80, b=100),  # Margem inferior aumentada para labels
        xaxis_title="",
        yaxis_title=config.get('original_value_column', 'Valor'),
        showlegend=False,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
    )

    # Personalizar barras com cores azuis harmoniosas
    fig.update_traces(
        marker_color='#3498db',  # Azul para comparações
        marker_line_color='#2980b9',  # Borda azul mais escura
        marker_line_width=1.5,
        opacity=0.85,
        textposition='outside',  # Posição dos rótulos acima das barras
        textfont=dict(size=11, color='#2c3e50', family='Arial')
    )

    # Configurações do eixo X para melhor legibilidade
    if is_categorical_id:
        # Forçar tratamento como categoria para códigos
        fig.update_xaxes(
            type='category',
            tickangle=-45,  # Inclinar labels para melhor legibilidade
            tickfont=dict(size=11, family='Arial')
        )
    else:
        # Comportamento padrão
        fig.update_xaxes(
            tickangle=-45,
            tickfont=dict(size=11, family='Arial')
        )

    # Configurações do eixo Y com formatação inteligente
    value_format = config.get('value_format', 'number')
    if value_format == 'currency':
        fig.update_yaxes(
            tickformat=',.0f',
            tickprefix='R$ ',
            tickfont=dict(size=10, family='Arial'),
            gridcolor='rgba(52, 152, 219, 0.2)',  # Grid sutil em azul
            gridwidth=1
        )
    else:
        fig.update_yaxes(
            tickformat=',.0f',
            tickfont=dict(size=10, family='Arial'),
            gridcolor='rgba(52, 152, 219, 0.2)',  # Grid sutil em azul
            gridwidth=1
        )

    # Ajustar título do gráfico com melhor estilo
    fig.update_layout(
        title_font=dict(size=16, family='Arial', color='#2c3e50'),
        title_x=0.5  # Centralizar título
    )

    # Renderizar o gráfico no Streamlit
    st.plotly_chart(fig, use_container_width=True, theme="streamlit")

    return True


def render_grouped_vertical_bar_chart(df, config):
    """
    Renderiza gráfico de barras verticais agrupadas para comparações entre poucos itens/períodos.
    Ideal para comparar 1-2 grupos (períodos/itens) com 2-5 categorias cada, usando cores distintas.

    Estrutura esperada do DataFrame:
    - 'group': Identificador do grupo/período (ex: "Março 2015", "Abril 2015")
    - 'category': Categoria dentro do grupo (ex: "SC", "PR", "RS")
    - 'value': Valor numérico

    Exemplo de uso:
    - "Vendas entre março/2015 e abril/2015 para SC, PR e RS"
    - Gráfico: 2 grupos (março, abril) × 3 barras coloridas (SC, PR, RS)
    """
    # Validar estrutura do DataFrame
    if 'group' not in df.columns or 'category' not in df.columns or 'value' not in df.columns:
        st.error(f"Erro: DataFrame para grouped_vertical_bar_chart deve ter colunas 'group', 'category' e 'value'. Recebido: {list(df.columns)}")
        return False

    # Preparar rótulos compactos para valores
    df_with_labels = df.copy()
    df_with_labels['value_label'] = df_with_labels['value'].apply(format_compact_number)

    # Validar limites (1-2 grupos, 2-5 categorias)
    n_groups = df_with_labels['group'].nunique()
    n_categories = df_with_labels['category'].nunique()

    if n_groups > 2:
        st.warning(f"Aviso: Muitos grupos ({n_groups}) para visualização comparativa. Limite: 2 grupos.")
        return False

    if n_categories > 5:
        st.warning(f"Aviso: Muitas categorias ({n_categories}) para visualização comparativa. Limite: 5 categorias.")
        return False

    if n_categories < 2:
        st.warning(f"Aviso: Poucas categorias ({n_categories}) para comparação. Mínimo: 2 categorias.")
        return False

    # Paleta de cores distintas para categorias (até 5)
    color_palette = [
        '#3498db',  # Azul
        '#e74c3c',  # Vermelho
        '#2ecc71',  # Verde
        '#f39c12',  # Laranja
        '#9b59b6'   # Roxo
    ]

    # Criar gráfico de barras verticais agrupadas
    fig = px.bar(
        df_with_labels,
        x='group',
        y='value',
        color='category',  # Cores distintas por categoria
        barmode='group',   # Barras agrupadas lado a lado
        title=config.get('title', 'Comparação entre Períodos/Itens'),
        labels={
            'value': config.get('y_label', 'Valor'),
            'group': config.get('x_label', 'Período/Item'),
            'category': 'Categoria'
        },
        text='value_label',  # Rótulos nos valores
        color_discrete_sequence=color_palette
    )

    # Configurações de layout
    fig.update_layout(
        height=550,  # Altura adequada para barras agrupadas
        margin=dict(l=60, r=50, t=90, b=140),  # Margem superior e inferior aumentadas
        xaxis_title=config.get('x_label', ''),
        yaxis_title=config.get('y_label', config.get('original_value_column', 'Valor')),
        showlegend=True,  # Mostrar legenda para identificar categorias
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        legend=dict(
            title=dict(text='', font=dict(size=12, family='Arial')),
            orientation='h',  # Legenda horizontal
            yanchor='bottom',
            y=-0.35,  # Mais abaixo para não sobrepor o título do eixo Y
            xanchor='center',
            x=0.5,
            bgcolor='rgba(255,255,255,0.9)',
            bordercolor='rgba(0,0,0,0.2)',
            borderwidth=1,
            font=dict(size=11, family='Arial')
        )
    )

    # Personalizar barras
    fig.update_traces(
        marker_line_width=1.5,
        marker_line_color='rgba(255,255,255,0.5)',
        opacity=0.9,
        textposition='outside',  # Rótulos acima das barras
        textfont=dict(size=11, color='#2c3e50', family='Arial')
    )

    # Configurações do eixo X
    fig.update_xaxes(
        tickfont=dict(size=12, family='Arial'),
        tickangle=0  # Sem inclinação para melhor legibilidade em comparações
    )

    # Configurações do eixo Y com formatação inteligente
    value_format = config.get('value_format', 'number')
    if value_format == 'currency':
        fig.update_yaxes(
            tickformat=',.0f',
            tickprefix='R$ ',
            tickfont=dict(size=10, family='Arial'),
            gridcolor='rgba(52, 152, 219, 0.2)',
            gridwidth=1
        )
    else:
        fig.update_yaxes(
            tickformat=',.0f',
            tickfont=dict(size=10, family='Arial'),
            gridcolor='rgba(52, 152, 219, 0.2)',
            gridwidth=1
        )

    # Ajustar título do gráfico
    fig.update_layout(
        title_font=dict(size=16, family='Arial', color='#2c3e50'),
        title_x=0.48,  # Centralizar título (ajustado para melhor posicionamento)
        title_xanchor='center'  # Ancorar ao centro para centralização perfeita
    )

    # Renderizar o gráfico no Streamlit
    st.plotly_chart(fig, use_container_width=True, theme="streamlit")

    return True


def render_line_chart(df, config):
    """
    Renderiza gráfico de linha para análise temporal.
    Suporta série única ou múltiplas séries (até 10).
    Retorna True se renderizou com sucesso, False caso contrário.
    """
    try:
        # Preparar dados para o gráfico de linha
        df_chart = df.copy()

        # Converter coluna de data para datetime se necessário
        try:
            df_chart['date'] = pd.to_datetime(df_chart['date'])
        except:
            pass  # Se não conseguir converter, usar como está

        # Detectar se é múltiplas séries
        has_multiple_series = 'category' in df_chart.columns

        if has_multiple_series:
            # MÚLTIPLAS SÉRIES: Gerar uma linha para cada categoria

            # Paleta de cores distinta para até 10 séries
            color_palette = [
                '#3498db',  # Azul
                '#e74c3c',  # Vermelho
                '#2ecc71',  # Verde
                '#f39c12',  # Laranja
                '#9b59b6',  # Roxo
                '#1abc9c',  # Turquesa
                '#e67e22',  # Laranja escuro
                '#34495e',  # Cinza azulado
                '#e91e63',  # Rosa
                '#00bcd4'   # Ciano
            ]

            # Criar gráfico com múltiplas linhas
            fig = px.line(
                df_chart,
                x='date',
                y='value',
                color='category',  # Separar por categoria
                title=config.get('title', 'Análise Temporal Comparativa'),
                labels={
                    'date': config.get('x_label', 'Data'),
                    'value': config.get('y_label', 'Valor'),
                    'category': 'Categoria'
                },
                markers=True,
                color_discrete_sequence=color_palette
            )

            # Configurações de layout para múltiplas séries
            fig.update_layout(
                height=550,
                margin=dict(l=50, r=50, t=60, b=50),
                xaxis_title=config.get('x_label', 'Data'),
                yaxis_title=config.get('y_label', 'Valor'),
                title_font=dict(size=16, family='Arial', color='#2c3e50'),
                title_x=0.5,
                hovermode='x unified',
                showlegend=True,
                legend=dict(
                    title=dict(text='', font=dict(size=12, family='Arial')),
                    orientation='v',
                    yanchor='top',
                    y=0.99,
                    xanchor='left',
                    x=1.01,
                    bgcolor='rgba(255,255,255,0.9)',
                    bordercolor='rgba(0,0,0,0.2)',
                    borderwidth=1,
                    font=dict(size=11, family='Arial')
                )
            )

            # Personalizar linhas
            fig.update_traces(
                line=dict(width=2.5),
                marker=dict(size=5, line=dict(width=1, color='white')),
                hovertemplate='<b>%{fullData.name}</b><br>Valor: %{y}<br>%{x}<extra></extra>'
            )

        else:
            # SÉRIE ÚNICA: Comportamento original

            # Formatar valores para exibição
            df_chart['value_label'] = df_chart['value'].apply(format_compact_number)

            # Criar gráfico de linha única
            fig = px.line(
                df_chart,
                x='date',
                y='value',
                title=config.get('title', 'Análise Temporal'),
                labels={
                    'date': config.get('x_label', 'Data'),
                    'value': config.get('y_label', 'Valor')
                },
                markers=True
            )

            # Configurações de layout para série única
            fig.update_layout(
                height=500,
                margin=dict(l=50, r=50, t=60, b=50),
                xaxis_title=config.get('x_label', 'Data'),
                yaxis_title=config.get('y_label') or config.get('original_value_column', 'Valor'),
                title_font=dict(size=16, family='Arial', color='#2c3e50'),
                title_x=0.5,
                hovermode='x',
                showlegend=False
            )

            # Personalizar linha única
            fig.update_traces(
                line=dict(width=3, color='#3498db'),
                marker=dict(size=6, color='#2980b9', line=dict(width=1, color='white')),
                hovertemplate='<b>%{y}</b><br>%{x}<extra></extra>'
            )

        # Configurar eixos (comum para ambos os casos)
        value_format = config.get('value_format', 'number')
        if value_format == 'currency':
            fig.update_yaxes(
                tickformat=',.0f',
                tickprefix='R$ ',
                tickfont=dict(size=11, family='Arial'),
                gridcolor='rgba(52, 152, 219, 0.2)',
                gridwidth=1
            )
        else:
            fig.update_yaxes(
                tickformat=',.0f',
                tickfont=dict(size=11, family='Arial'),
                gridcolor='rgba(52, 152, 219, 0.2)',
                gridwidth=1
            )

        fig.update_xaxes(
            tickfont=dict(size=11, family='Arial'),
            gridcolor='rgba(52, 152, 219, 0.1)',
            gridwidth=1
        )

        # Renderizar no Streamlit
        st.plotly_chart(fig, use_container_width=True, theme="streamlit")

        return True

    except Exception as e:
        st.error(f"Erro ao renderizar gráfico de linha: {str(e)}")
        return False