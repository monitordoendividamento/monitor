import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import os
import warnings
import datetime
import calendar
import json
import requests
from dash import Dash, dcc, html, Input, Output
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime as dt, timedelta

warnings.filterwarnings('ignore')

st.set_page_config(page_title="Monitor endividamento", page_icon=":bar_chart:", layout="wide", initial_sidebar_state="collapsed", menu_items={"About": "Link ou descrição aqui"})


#Desabilitar o hover no celular

disable_hover_plotly_css = """
<style>
@media (hover: none), (pointer: coarse) {
    /* Desativar hover nos elementos Plotly com a classe 'nsewdrag drag' */
    .nsewdrag.drag {
        pointer-events: none !important;
    }
}
</style>
"""

# Adicionando o CSS na aplicação
st.markdown(disable_hover_plotly_css, unsafe_allow_html=True)

#Início da página

st.title(" :bar_chart: Monitor do endividamento dos brasileiros")

st.info('Para facilitar a sua análise, todos os valores já estão a valores presentes!\n\n'
        'Clique em "sobre" no canto superior direito da tela para conferir mais detalhes sobre este projeto', 
        icon="👩‍💻")

#Caixa para selecionar as datas

st.sidebar.header("Qual período você deseja consultar?")
diferentes_dividas = pd.read_csv("analise_divida_tempo.csv", encoding="UTF-8", delimiter=',', decimal='.')
diferentes_dividas["data_base"] = pd.to_datetime(diferentes_dividas["data_base"], format='%Y-%m-%d')

min_year = int(diferentes_dividas['data_base'].dt.year.min())
max_year = int(diferentes_dividas['data_base'].dt.year.max())

min_month = int(diferentes_dividas['data_base'].dt.month.min())
max_month = int(diferentes_dividas['data_base'].dt.month.max())

month_abbr = list(calendar.month_abbr) 

def select_month_and_year(name, min_year, max_year, default_month, default_year):
    with st.sidebar.expander(name):
        year = st.selectbox(f'{name} - Ano', range(max_year, min_year - 1, -1), index=max_year - default_year)
        month = st.selectbox(f'{name} - Mês', month_abbr[1:], index=default_month - 1) 
    return month, year

start_month, start_year = select_month_and_year('Data de Início', min_year, max_year, min_month, min_year)
end_month, end_year = select_month_and_year('Data Final', min_year, max_year, max_month, max_year)

date1 = datetime.datetime(start_year, month_abbr.index(start_month), 1)
last_day = calendar.monthrange(end_year, month_abbr.index(end_month))[1]
date2 = datetime.datetime(end_year, month_abbr.index(end_month), last_day)

st.sidebar.markdown(f'<p style="text-align: center">Exibindo dados para o intervalo {date1.strftime("%Y-%m")} a {date2.strftime("%Y-%m")}.</p>', unsafe_allow_html=True)

st.subheader("Como a população brasileira anda se endividando?")

st.markdown("<div style='text-align: center; color: #555555; font-size: 1.3em;'>Endividamento dos brasileiros pessoas físicas de acordo com a sua ocupação</div>", unsafe_allow_html=True)

@st.cache_data()
def load_data():
    data = pd.read_csv("pf_ocupacao_modalidade_endividamento.csv", encoding="UTF-8", delimiter=',', decimal='.')
    data["data_base"] = pd.to_datetime(data["data_base"], format='%Y-%m-%d')
    return data

@st.cache_data()
def filter_data(data, date1, date2, ocupacao):
    filtered_data = data[(data["data_base"] >= date1) & (data["data_base"] <= date2)]
    if ocupacao is not None:
        filtered_data = filtered_data[filtered_data['ocupacao'] == ocupacao]
    return filtered_data

pf_ocupacao_modalidade_endividamento = load_data()

ocupacao = st.selectbox(
    'Para qual ocupação você deseja visualizar?',
    pf_ocupacao_modalidade_endividamento['ocupacao'].unique()
)

pf_ocupacao_modalidade_endividamento_filtrado = filter_data(pf_ocupacao_modalidade_endividamento, date1, date2, ocupacao)

col1, col2 = st.columns((2))

with col1:

    # Criação do gráfico
    plot_pf_ocupacao_modalidade_endividamento = px.line(pf_ocupacao_modalidade_endividamento_filtrado, 
                                                        x='data_base',
                                                        y='carteira_ativa_deflacionada', 
                                                        color='modalidade')

    plot_pf_ocupacao_modalidade_endividamento.update_layout(
        title_text='',
        xaxis_title='',
        yaxis_title='Endividamento total',
        template="seaborn",
        legend=dict(
            x=0.5,
            y=-0.3,
            orientation='h',
            xanchor='center'
        ),
        xaxis=dict(showgrid=False),
        margin=dict(t=0, b=0, l=0, r=0)
    )
    plot_pf_ocupacao_modalidade_endividamento.update_yaxes(showgrid=False)

    st.plotly_chart(plot_pf_ocupacao_modalidade_endividamento, use_container_width=True)

with col2:
    
    st.markdown("<div style='text-align: center; color: #888888; font-size: 0.9em;'>Estados federativos em que residem os tomadores de crédito com parcelas classificadas como ativo problemático, em que há pouca expectativa de pagamento</div>", unsafe_allow_html=True)
    
    @st.cache_data()
    def load_df_ocupacao_pf_ativoproblematico():
        return pd.read_csv("df_ocupacao_pf_ativoproblematico.csv", encoding="UTF-8", delimiter=',', decimal='.')

    @st.cache_data()
    def load_geojson_data():
        url = "https://raw.githubusercontent.com/jonates/opendata/master/arquivos_geoespaciais/unidades_da_federacao.json"
        response = requests.get(url)
        return response.json()

    df_ocupacao_pf_ativoproblematico = load_df_ocupacao_pf_ativoproblematico()
    geojson_data = load_geojson_data()
    
    df_ocupacao_pf_ativoproblematico_filtered = df_ocupacao_pf_ativoproblematico[df_ocupacao_pf_ativoproblematico['ocupacao'] == ocupacao]

    plot_ocupacao_pf_ativoproblematico = px.choropleth_mapbox(df_ocupacao_pf_ativoproblematico_filtered, 
                                   geojson=geojson_data, 
                                   locations='Estado', 
                                   color='ativo_problematico/pop',
                                   color_continuous_scale="sunsetdark",
                                   range_color=(0, max(df_ocupacao_pf_ativoproblematico_filtered['ativo_problematico/pop'])),
                                   animation_frame='ano', 
                                   mapbox_style="open-street-map",
                                   zoom=1.9, 
                                   center={"lat": -17.14, "lon": -57.33},
                                   opacity=1,
                                   labels={'ativo_problematico/pop':'Ativo problemático/População',
                                           'uf': 'Unidade da Federação do Brasil'},
                                   featureidkey="properties.NM_ESTADO")

    plot_ocupacao_pf_ativoproblematico.update_layout(
        coloraxis_colorbar=dict(
            len=1, 
            y=-0.25,  
            yanchor='bottom',  
            xanchor='center',
            x=0.5,   
            orientation='h',  
            title="ativo problemático/população",
            titleside = "bottom"
        ),
            margin=dict(t=0, b=0, l=0, r=0)
    )


    st.plotly_chart(plot_ocupacao_pf_ativoproblematico,use_container_width=True)

st.markdown("<div style='text-align: center; color: #555555; font-size: 1.3em;'>Endividamento dos brasileiros pessoas físicas de acordo com a sua renda</div>", unsafe_allow_html=True)

@st.cache_data()
def load_pf_rendimento_modalidade_noperacoes_endividamento():
    df = pd.read_csv("pf_rendimento_modalidade_noperacoes_endividamento.csv", encoding="UTF-8", delimiter=',', decimal='.')
    df["data_base"] = pd.to_datetime(df["data_base"], format='%Y-%m-%d')
    return df

pf_rendimento_modalidade_noperacoes_endividamento = load_pf_rendimento_modalidade_noperacoes_endividamento()

pf_rendimento_modalidade_noperacoes_endividamento_filtrado = pf_rendimento_modalidade_noperacoes_endividamento[(pf_rendimento_modalidade_noperacoes_endividamento["data_base"] >= date1) & (pf_rendimento_modalidade_noperacoes_endividamento["data_base"] <= date2)].copy()


porte = st.selectbox(
    "Para qual faixa rendimento você deseja visualizar?",
    pf_rendimento_modalidade_noperacoes_endividamento_filtrado['porte'].unique()
)

col20, col21 = st.columns((2))

with col20:
    st.markdown("<div style='text-align: center; color: #888888; font-size: 0.9em;'>Endividamento com vencimento acima de 360 dias em relação às modalidades de crédito contratadas pelas pessoas físicas da faixa de renda selecionada</div>", unsafe_allow_html=True)
    
    pf_rendimento_modalidade_noperacoes_endividamento_filtrado = pf_rendimento_modalidade_noperacoes_endividamento_filtrado[pf_rendimento_modalidade_noperacoes_endividamento_filtrado['porte'] == porte]

    plot_rendimento_modalidade_noperacoes = px.line(pf_rendimento_modalidade_noperacoes_endividamento_filtrado, 
                  x='data_base', 
                  y='longo_prazo_deflacionado', 
                  color='modalidade')

    plot_rendimento_modalidade_noperacoes.update_layout(
    title_text='',
    xaxis_title='',
    yaxis_title='Endividamento de longo prazo',
    template="seaborn",
    legend=dict(
        x=0.5,
        y=-0.3,
        orientation='h',
        xanchor='center'
    ),
    xaxis=dict(showgrid=False),
    yaxis=dict(
        showgrid=False, 
        title='Endividamento de longo prazo'
    ),
    margin=dict(t=0, b=0, l=0, r=0)
)

    st.plotly_chart(plot_rendimento_modalidade_noperacoes, use_container_width=True)

with col21:
    
    st.markdown("<div style='text-align: center; color: #888888; font-size: 0.9em;'>Quantidade de operações totais (para qualquer vencimento) em relação às modalidades de crédito contratadas pelas pessoas físicas da faixa de renda selecionada</div>", unsafe_allow_html=True)

    pf_rendimento_modalidade_noperacoes_endividamento_filtrado = pf_rendimento_modalidade_noperacoes_endividamento_filtrado[pf_rendimento_modalidade_noperacoes_endividamento_filtrado['porte'] == porte]

    plot_rendimento_modalidade_noperacoes = px.line(pf_rendimento_modalidade_noperacoes_endividamento_filtrado, 
                  x='data_base', 
                  y='numero_de_operacoes', 
                  color='modalidade')

    plot_rendimento_modalidade_noperacoes.update_layout(
        title_text='',
        xaxis_title='',
        yaxis_title='Número de operações',
        template="seaborn",
        legend=dict(
            x=0.5,
            y=-0.3,
            orientation='h',
            xanchor='center'
        ),
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=False),
        margin=dict(t=0, b=0, l=0, r=0)
    )
        
    st.plotly_chart(plot_rendimento_modalidade_noperacoes, use_container_width=True)

st.markdown("<div style='text-align: center; color: #555555; font-size: 1.3em;'>Inserindo dados macroeconômicos na análise</div>", unsafe_allow_html=True)

@st.cache_data()
def load_df_juros_inflacao_modalidade():
    df = pd.read_csv("df_juros_inflacao_modalidade.csv", encoding="UTF-8", delimiter=',', decimal='.')
    df["data_base"] = pd.to_datetime(df["data_base"], format='%Y-%m')
    return df

df_juros_inflacao_modalidade = load_df_juros_inflacao_modalidade()

df_juros_inflacao_modalidade_filtrado = df_juros_inflacao_modalidade[(df_juros_inflacao_modalidade["data_base"] >= date1) & (df_juros_inflacao_modalidade["data_base"] <= date2)].copy()

def create_figure(yaxis_column_name):
    plot_juros_inflacao_modalidade = go.Figure()

    for modalidade in df_juros_inflacao_modalidade_filtrado['modalidade'].unique():
        subset = df_juros_inflacao_modalidade_filtrado[df_juros_inflacao_modalidade_filtrado['modalidade'] == modalidade]
        plot_juros_inflacao_modalidade.add_trace(go.Scatter(x=subset['data_base'],
                                     y=subset['longo_prazo_deflacionado'],
                                     mode='lines',
                                     name=f'{modalidade}',
                                     yaxis='y2',
                                     opacity=0.7,
                                     line=dict(width=2)))

    plot_juros_inflacao_modalidade.add_trace(go.Scatter(x=df_juros_inflacao_modalidade_filtrado['data_base'],
                                 y=df_juros_inflacao_modalidade_filtrado[yaxis_column_name],
                                 mode='lines',
                                 opacity=1,
                                 name=yaxis_column_name,
                                 line=dict(color='dimgray', width=2, dash='dot')))

    plot_juros_inflacao_modalidade.update_layout(
        yaxis2=dict(
            overlaying='y',
            side='right',
            showgrid=False,
            title="Endividamento de longo prazo"
        ),
        legend_title_text='modalidades',
        template="seaborn",
        legend=dict(
            x=0.5,
            y=-0.2,
            orientation='h',
            xanchor='center',
            traceorder='normal',
            yanchor='top',
            font=dict(
            size=12
            )
        ),
        xaxis=dict(showgrid=False),
        yaxis=dict(
            showgrid=False,
            title=yaxis_column_name
        ),
        margin=dict(t=0, l=0, r=0, b=0),
        showlegend = True
    )
        
    return plot_juros_inflacao_modalidade

option = st.selectbox(
        'Selecione o indicador macroeconômico que você deseja adicionar à série',
        ('IPCA', 'Taxa média mensal de juros - PF')
    )
    
st.markdown("<div style='text-align: center; color: #888888; font-size: 0.9em;'>Distribuição do endividamento com parcelas acima de 360 dias por modalidades de contratação</div>", unsafe_allow_html=True)

st.plotly_chart(create_figure(option), use_container_width=True)


col30, col31 = st.columns((2))

with col30:
    
    st.markdown("<div style='text-align: center; color: #888888; font-size: 0.9em;'>Endividamento com vencimento acima de 360 dias por faixa de renda em comparação à taxa de desocupação</div>", unsafe_allow_html=True)
    
 
    @st.cache_data()
    def load_desemprego_divida_lp():
        df = pd.read_csv("df_desemprego_divida_grupo.csv", encoding="UTF-8", delimiter=',', decimal='.')
        df["data"] = pd.to_datetime(df["data"], format='%Y-%m')
        return df
    
    desemprego_divida_lp = load_desemprego_divida_lp()

    desemprego_divida_lp_filtrado = desemprego_divida_lp[(desemprego_divida_lp["data"] >= date1) & (desemprego_divida_lp["data"] <= date2)].copy()

    plot_desemprego_divida_lp_filtrado = go.Figure()

    for categoria_renda in desemprego_divida_lp_filtrado['categoria_renda'].unique():
        subset = desemprego_divida_lp_filtrado[desemprego_divida_lp_filtrado['categoria_renda'] == categoria_renda]
        plot_desemprego_divida_lp_filtrado.add_trace(go.Scatter(x=subset['data'],
                                 y=subset['longo_prazo_deflacionado'],
                                 mode='lines',
                                 name=f'{categoria_renda}',
                                 yaxis='y2',
                                 opacity=0.7))

    plot_desemprego_divida_lp_filtrado.add_trace(go.Scatter(x=desemprego_divida_lp_filtrado['data'],
                             y=desemprego_divida_lp_filtrado['valor'], 
                             mode='lines',
                             name='taxa de desocupação',
                             opacity=1,
                            line=dict(color='dimgray', width=2, dash='dot')))

    plot_desemprego_divida_lp_filtrado.add_shape(
        go.layout.Shape(
            type="line",
            x0="2017-07-01",
            x1="2017-07-01",
            y0=0,
            y1=1,
            yref='paper',
            line=dict(color="black", width=2)
        )
    )

    plot_desemprego_divida_lp_filtrado.add_annotation(
        go.layout.Annotation(
            text="Reforma Trabalhista",
            x="2017-07-01",
            y=0,
            yref='paper',
            showarrow=False,
            font=dict(color="black", size=12),
            textangle = 90,
            xshift=10
        )
    )

    plot_desemprego_divida_lp_filtrado.update_layout(
        yaxis2=dict(
            overlaying='y',
            side='right',
            showgrid=False,
            title="Endividamento de longo prazo"
        ),
        template="seaborn",
        legend_title_text='categorias de renda',
        legend=dict(
            x=0.5,  # Centraliza a legenda no eixo x
            y=-0.2,
            traceorder='normal',
            orientation='h',
            xanchor='center',  # Ancora o centro da legenda no ponto x
            yanchor='top'      # Ancora a parte superior da legenda no ponto y
        ),  
        xaxis=dict(showgrid=False),
        yaxis=dict(
            showgrid=False,
            title="Taxa de desocupação"
        ),
        showlegend = True,
        margin=dict(t=0, b=0, l=0, r=0)
    )

    st.plotly_chart(plot_desemprego_divida_lp_filtrado, use_container_width=True)
    
with col31:
    
    st.markdown("<div style='text-align: center; color: #888888; font-size: 0.9em;'>Correlação entre indicadores macroeconômicos e as parcelas do endividamento total e parcelas com pouca expectativa de pagamento</div>", unsafe_allow_html=True)
    

    @st.cache_data()
    def load_df_corr_porte_pf():
        df = pd.read_csv("df_corr_porte_pf.csv", encoding="UTF-8", delimiter=',', decimal='.')
        return df

    df_corr_porte_pf = load_df_corr_porte_pf()

    sns.set_theme(style="white")
    corr = df_corr_porte_pf.corr()
    mask = np.triu(np.ones_like(corr, dtype=bool))
    plot_corr_porte_pf, ax = plt.subplots()
    sns_heatmap = sns.heatmap(corr, mask=mask, cmap='RdBu',
                          square=True, linewidths=.5, annot=True, annot_kws={"size": 10}, cbar_kws={"shrink": 0.8},
                          cbar=True)  

    ax.xaxis.tick_bottom()
    ax.set_xticklabels(ax.get_xticklabels(), rotation=90)
    ax.xaxis.set_label_position('bottom') 

    # Mover os rótulos do eixo Y para a direita
    ax.yaxis.tick_left()
    ax.set_yticklabels(ax.get_yticklabels(), rotation=0)
    ax.yaxis.set_label_position('left')

    # Ajustes adicionais
    ax.tick_params(axis='both', which='both', labelsize=7, color='#888888')
    
    cbar = ax.collections[0].colorbar
    cbar.ax.tick_params(labelsize=9, color='#888888')
    
    plot_corr_porte_pf.patch.set_alpha(0)
    ax.set_facecolor('none')

    st.pyplot(plot_corr_porte_pf, use_container_width=True)

st.markdown("<div style='text-align: center; color: #888888; font-size: 0.9em;'>Endividamento com prazo de vencimento acima de 360 dias em comparação ao índice de preços ao consumidor amplo (inflação)</div>", unsafe_allow_html=True)


@st.cache_data()
def load_pf_porte_endividamentolp_inflacao():
    df = pd.read_csv("pf_porte_endividamentolp_inflacao.csv", encoding="UTF-8", delimiter=',', decimal='.')
    df["data"] = pd.to_datetime(df["data"], format='%Y-%m')
    return df

pf_porte_endividamentolp_inflacao = load_pf_porte_endividamentolp_inflacao()

pf_porte_endividamentolp_inflacao_filtrado = pf_porte_endividamentolp_inflacao[(pf_porte_endividamentolp_inflacao["data"] >= date1) & (pf_porte_endividamentolp_inflacao["data"] <= date2)].copy()

plot_pf_porte_endividamentolp_inflacao = go.Figure()

for porte in pf_porte_endividamentolp_inflacao_filtrado['porte'].unique():
    subset = pf_porte_endividamentolp_inflacao_filtrado[pf_porte_endividamentolp_inflacao_filtrado['porte'] == porte]
    
    plot_pf_porte_endividamentolp_inflacao.add_trace(go.Scatter(
        x=subset['data_divida'],
        y=subset['valor_deflacionado'],
        mode='lines',
        opacity=0.7,
        name=f'{porte}',
        yaxis='y2'
    ))

plot_pf_porte_endividamentolp_inflacao.add_trace(go.Scatter(
    x=pf_porte_endividamentolp_inflacao_filtrado['data_divida'],
    y=pf_porte_endividamentolp_inflacao_filtrado['valor'],
    opacity=1,
    line=dict(color='dimgray', width=2, dash='dot'),
    mode='lines',
    name='IPCA'
))

plot_pf_porte_endividamentolp_inflacao.update_layout(
    yaxis=dict(
        title="IPCA",
        showgrid=False
    ),
    yaxis2=dict(
        title="Endividamento de longo prazo",
        overlaying='y',
        side='right',
        showgrid=False
    ),
    xaxis=dict(
        showgrid=False,
        dtick="M24"
    ),
    legend=dict(
        x=0.5,
        y=-0.2,
        traceorder='normal',
        orientation='h',
        xanchor='center',
        yanchor='top',
        font=dict(size=12)
    ),
    template="seaborn",
    showlegend = True,
    legend_title_text='modalidade'
)

st.plotly_chart(plot_pf_porte_endividamentolp_inflacao, use_container_width=True)

#Mapa endividamento PF e PJ
st.subheader('Como as empresas andam se financiando?')

st.markdown("<div style='text-align: center; color: #555555; font-size: 1.3em;'>Distribuição dos ativos problemáticos das empresas brasileiras, em que há pouca expectativa de pagamento</div>", unsafe_allow_html=True)

@st.cache_data()
def load_df_corr_ibge_scr_pj():
    df = pd.read_csv("df_corr_ibge_scr_pj.csv", encoding="UTF-8", delimiter=',', decimal='.')
    return df

df_corr_ibge_scr_pj = load_df_corr_ibge_scr_pj()

cnae_secao = st.selectbox(
        'Para qual setor de atuação você deseja visualizar?',
        df_corr_ibge_scr_pj['cnae_secao'].unique()
    )
    
col5, col6 = st.columns((2))

with col5:

    st.markdown("<div style='text-align: center; color: #888888; font-size: 0.9em;'>Dispersão entre os ativos problemáticos e a saída das empresas que pertencem ao setor de atuação selecionado</div>", unsafe_allow_html=True)
    
    df_corr_ibge_scr_pj_filtered = df_corr_ibge_scr_pj[df_corr_ibge_scr_pj['cnae_secao'] == cnae_secao]

    plot_corr_ibge_scr_pj = px.scatter(df_corr_ibge_scr_pj_filtered, x="ativo_problematico", y="Saída de atividade/Total", color="cnae_secao", hover_data=["Seção CNAE e ano"])
    
    plot_corr_ibge_scr_pj.update_layout(showlegend=False,
                                       title='',
                                        margin=dict(t=0, l=0, r=0, b=0),
                                        template = "seaborn",
                                       xaxis_title='Ativo problemático',
                                       xaxis=dict(showgrid=False))
    
    plot_corr_ibge_scr_pj.update_yaxes(showgrid=False)
    
    st.plotly_chart(plot_corr_ibge_scr_pj, use_container_width=True)


with col6:
    
    st.markdown("<div style='text-align: center; color: #888888; font-size: 0.9em;'>Estados federativos em que estão localizadas as empresas tomadoras de crédito com parcelas classificadas como ativo problemático que pertencem ao setor de atuação selecionado</div>", unsafe_allow_html=True)
    
    @st.cache_data()
    def load_df_cnae_pj_ativoproblematico():
        df = pd.read_csv("df_cnae_pj_ativoproblematico.csv", encoding="UTF-8", delimiter=',', decimal='.')
        return df
    
    df_cnae_pj_ativoproblematico = load_df_cnae_pj_ativoproblematico()

    df_cnae_pj_ativoproblematico_filtered = df_cnae_pj_ativoproblematico[df_cnae_pj_ativoproblematico['cnae_secao'] == cnae_secao]

    plot_cnae_pj_ativoproblematico = px.choropleth_mapbox(df_cnae_pj_ativoproblematico_filtered, 
                               geojson=geojson_data, 
                               locations='Estado', 
                               color='ativo_problematico/pop',
                               color_continuous_scale="sunsetdark",
                               range_color=(0, max(df_cnae_pj_ativoproblematico_filtered['ativo_problematico/pop'])),
                               animation_frame='ano', 
                               mapbox_style="open-street-map",
                               zoom=1.9, 
                               center={"lat": -17.14, "lon": -57.33},
                               opacity=1,
                               labels={'ativo_problematico/pop':'Ativo problemático',
                                       'uf': 'Unidade da Federação do Brasil'},
                               featureidkey="properties.NM_ESTADO")
    
    plot_cnae_pj_ativoproblematico.update_layout(
    coloraxis_colorbar=dict(
        len=1,
        y=-0.25,  
        yanchor='bottom',  
        xanchor='center',
        x=0.5,   
        orientation='h',  
        title="ativo problemático/população",
        titleside = "bottom"
    ),
        margin=dict(t=0, b=0, l=0, r=0)
)

    
    st.plotly_chart(plot_cnae_pj_ativoproblematico,use_container_width=True)

st.markdown("<div style='text-align: center; color: #555555; font-size: 1.3em;'>Por dentro das micro e pequenas empresas</div>", unsafe_allow_html=True)
    
st.markdown("<div style='text-align: center; color: #888888; font-size: 0.9em;'>Modalidades de crédito contratadas pelas micro e pequenas empresas com parcelas cujo vencimento é inferior a 360 dias</div>", unsafe_allow_html=True)

@st.cache_data()
def load_pj_porte_modalidade_endividamentocp():
    df = pd.read_csv("pj_porte_modalidade_endividamentocp.csv", encoding="UTF-8", delimiter=',', decimal='.')
    df["data_base"] = pd.to_datetime(df["data_base"], format='%Y-%m')
    # Adicione aqui qualquer processamento adicional necessário
    return df

pj_porte_modalidade_endividamentocp = load_pj_porte_modalidade_endividamentocp()

pj_porte_modalidade_endividamentocp_filtrado = pj_porte_modalidade_endividamentocp[(pj_porte_modalidade_endividamentocp["data_base"] >= date1) & (pj_porte_modalidade_endividamentocp["data_base"] <= date2)].copy()

plot_pj_porte_modalidade_endividamentocp = px.line(pj_porte_modalidade_endividamentocp_filtrado, 
             x='data_base', 
             y='curto_prazo_deflacionado',
              color = 'modalidade',
             facet_col='porte',
             title='',
             labels={'data_base': '', 'curto_prazo_deflacionado': 'Endividamento de curto prazo'},
             template="seaborn",
             category_orders={"porte": ["Empresa de pequeno porte", "Microempresa"]})

plot_pj_porte_modalidade_endividamentocp.update_layout(
    yaxis_title="Endividamento de curto prazo",
    legend_title_text='modalidade',
    legend=dict(x=0.5, y=-0.17, xanchor='center', yanchor='top', orientation = 'h'),
    xaxis=dict(dtick="M24"),
    xaxis2=dict(dtick="M24")
)

st.plotly_chart(plot_pj_porte_modalidade_endividamentocp, use_container_width=True)

st.markdown("<div style='text-align: center; color: #888888; font-size: 0.9em;'>Micro e pequenas empresas: endividamento para capital de giro versus ativo problemático, em que há pouca expectativa de pagamento</div>", unsafe_allow_html=True)

df_micro_peq_problematico = pd.read_csv("df_micro_peq_problematico.csv", encoding="UTF-8", delimiter=',', decimal='.')

df_micro_peq_problematico["data_base"] = pd.to_datetime(df_micro_peq_problematico["data_base"], format='%Y-%m-%d')

df_micro_peq_problematico_filtrado = df_micro_peq_problematico[(df_micro_peq_problematico["data_base"] >= date1) & (df_micro_peq_problematico["data_base"] <= date2)].copy()

df_micro_peq_problematico = df_micro_peq_problematico.rename(columns={
    'curto_prazo_deflacionado': 'Endividamento de Curto Prazo',
    'ativo_problematico_deflacionado': 'Ativo Problemático'
})

plot_micro_peq_problematico = px.bar(df_micro_peq_problematico, 
             x='data_base', 
             y=['Endividamento de Curto Prazo', 'Ativo Problemático'],
             facet_col='porte', 
             labels={'data_base': ''},
             template="seaborn")

plot_micro_peq_problematico.update_layout(
    barmode='group',
    yaxis_title="Endividamento de curto prazo e ativo problemático, em que há pouca expectativa de pagamento",
    legend_title_text='tipo de endividamento',
    legend=dict(x=0.5, y=-0.15, xanchor='center', yanchor='top', orientation = 'h'),
        xaxis=dict(dtick="M24"),
        xaxis2=dict(dtick="M24")
)

st.plotly_chart(plot_micro_peq_problematico, use_container_width=True)

st.markdown("<div style='text-align: center; color: #555555; font-size: 1.3em;'>Por dentro do setor de agricultura, pecuária, produção florestal, pesca e aquicultura</div>", unsafe_allow_html=True)

st.markdown("<div style='text-align: center; color: #888888; font-size: 0.9em;'>Distribuição do endividamento nas principais áreas de atuação das empresas do setor de agricultura, pecuária, produção florestal, pesca e aquicultura em dezembro-2022</div>", unsafe_allow_html=True)


@st.cache_data()
def load_pj_cnaesecao_cnaesubclasse_endividamento():
    df = pd.read_csv("pj_cnaesecao_cnaesubclasse_endividamento.csv", encoding="UTF-8", delimiter=',', decimal='.')
    df["data_base"] = pd.to_datetime(df["data_base"], format='%Y-%m')
    return df

pj_cnaesecao_cnaesubclasse_endividamento = load_pj_cnaesecao_cnaesubclasse_endividamento()

pj_cnaesecao_cnaesubclasse_endividamento_filtrado = pj_cnaesecao_cnaesubclasse_endividamento[(pj_cnaesecao_cnaesubclasse_endividamento["data_base"] >= date1) & (pj_cnaesecao_cnaesubclasse_endividamento["data_base"] <= date2)].copy()

plot_pj_cnaesecao_cnaesubclasse_endividamento = px.treemap(pj_cnaesecao_cnaesubclasse_endividamento_filtrado, 
                 path=['cnae_secao', 'cnae_subclasse'],
                 values='valor_deflacionado')

plot_pj_cnaesecao_cnaesubclasse_endividamento.update_layout(title='',
                  margin=dict(t=0, l=0, r=0, b=0),
                 template = "seaborn")

plot_pj_cnaesecao_cnaesubclasse_endividamento.update_traces(textinfo='label+percent entry',
                 marker_line_width = 1,
                 hovertemplate='%{label} <br> $%{value:,.2f} <br> Percentual: %{percentRoot:.2%}',
                 textposition="top left",
                 textfont_size = 12,
                 textfont_color = 'white')

st.plotly_chart(plot_pj_cnaesecao_cnaesubclasse_endividamento,use_container_width=True)

st.subheader("Como esse assunto vem sendo tratado pelos legisladores?")

st.markdown("<div style='text-align: center; color: #555555; font-size: 1.3em;'>Proposições legislativas com tramitação nos últimos 360 anos que se referem à endividamento</div>", unsafe_allow_html=True)

st.markdown("<div style='text-align: center; color: #666666; font-size: 1em;'>A busca utiliza a API da Câmara dos Deputados, módulo proposições, e se refere aos projetos de lei e medidas provisórias que tenham como palavras-chave termos relacionados ao endividamento da população brasileira.</div>", unsafe_allow_html=True)

#API Camara dos deputados

@st.cache_data(ttl=3600)
def fetch_projetos(data_inicio, data_fim, palavras_chave):
    url = "https://dadosabertos.camara.leg.br/api/v2/proposicoes"
    params = {
        "dataInicio": data_inicio,
        "dataFim": data_fim,
        "ordenarPor": "id",
        "itens": 100,
        "pagina": 1,
        "siglaTipo": ["PL", "PLP", "MPV"],
        "keywords": palavras_chave
    }

    projetos = []
    while True:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            dados = response.json()["dados"]
            if len(dados) == 0:
                break
            projetos.extend(dados)
            params["pagina"] += 1
        else:
            print("Erro ao fazer requisição para a API:", response.status_code)
            break
    return projetos

@st.cache_data(ttl=3600)
def fetch_tramitacoes(id_proposicao, token):
    url_tramitacoes = f"https://dadosabertos.camara.leg.br/api/v2/proposicoes/{id_proposicao}/tramitacoes"
    response_tramitacoes = requests.get(url_tramitacoes, headers={"Authorization": f"Bearer {token}"})
    if response_tramitacoes.status_code == 200:
        tramitacoes = response_tramitacoes.json()['dados']
        ultima_tramitacao = tramitacoes[-1] if tramitacoes else None
        return ultima_tramitacao['descricaoSituacao'] if ultima_tramitacao else "Sem tramitações"
    else:
        print(f"Erro ao obter as tramitações da proposição {id_proposicao}: {response_tramitacoes.status_code}")
        return "Erro na tramitação"

def create_dataframe(projetos, token):
    for proposicao in projetos:
        id_proposicao = proposicao['id']
        situacao_tramitacao = fetch_tramitacoes(id_proposicao, token)
        proposicao['situacaoTramitacao'] = situacao_tramitacao

    colunas = ['siglaTipo', 'numero', 'ano', 'ementa', 'situacaoTramitacao']
    df = pd.DataFrame(projetos, columns=colunas)
    df['situacaoTramitacao'] = df['situacaoTramitacao'].astype('str')
    df['situacaoTramitacao'] = df['situacaoTramitacao'].replace(to_replace='None', value='Não informado')
    
    df['ano'] = df['ano'].astype('int')
    df['numero'] = df['numero'].astype('int')
    df['numero'] = df['numero'].apply(lambda x: f"{x:,}".replace(',', '.'))
    df.columns = ["Tipo", "Número", "Ano", "Ementa", "Situação"]
    return df

token = "seu_token_de_acesso_aqui"
data_inicio = (datetime.datetime.now() - datetime.timedelta(days=180)).strftime("%Y-%m-%d")
data_fim = datetime.datetime.now().strftime("%Y-%m-%d")
palavras_chave = [ 
"superendividamento",
"inadimplimento das obrigações", 
"mínimo existencial",   
"repactuação de dívidas",
"taxa de juros"
"crédito ao consumidor",
"parcelamento de dívidas",
"renegociação de dívidas"
"rotativo"
"cartão de crédito",
"crédito rural",
"crédito habitacional",
"empréstimo consignado"
"capital de giro",
"crédito para investimento",
"sistemas de informação de crédito",
"ativo problemático",
"crédito a vencer"
]

projetos = fetch_projetos(data_inicio, data_fim, palavras_chave)

df = create_dataframe(projetos, token)

def filter_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    # Inicializar os estados dos filtros apenas uma vez
    if 'filter_initialized' not in st.session_state:
        st.session_state.filter_tipo = df['Tipo'].unique().tolist()
        st.session_state.filter_ano = (int(df['Ano'].min()), int(df['Ano'].max()))
        st.session_state.filter_situacao = df['Situação'].unique().tolist()
        st.session_state.filter_initialized = True

    modify = st.checkbox("Filtrar o resultado")

    if not modify:
        return df

    with st.container():
        # Filtro para o Tipo
        selected_tipo = st.multiselect(
            "Filter Tipo",
            df['Tipo'].unique(),
            default=st.session_state.filter_tipo
        )

        # Filtro para o Ano
        _min, _max = int(df['Ano'].min()), int(df['Ano'].max())
        selected_ano = st.slider(
            "Filter Ano",
            min_value=_min,
            max_value=_max,
            value=st.session_state.filter_ano,
            step=1
        )

        # Filtro para a Situação
        selected_situacao = st.multiselect(
            "Filter Situação",
            df['Situação'].unique(),
            default=st.session_state.filter_situacao
        )

    # Aplicar filtros
    if selected_tipo != st.session_state.filter_tipo:
        df = df[df['Tipo'].isin(selected_tipo)]
        st.session_state.filter_tipo = selected_tipo

    if selected_ano != st.session_state.filter_ano:
        df = df[df['Ano'].between(*selected_ano)]
        st.session_state.filter_ano = selected_ano

    if selected_situacao != st.session_state.filter_situacao:
        df = df[df['Situação'].isin(selected_situacao)]
        st.session_state.filter_situacao = selected_situacao

    return df

filtered_df = filter_dataframe(df)

def formatar_numero(valor):
    return f"{valor}"

dados_formatados = filtered_df.style.format({'Número': formatar_numero})

st.dataframe(dados_formatados, use_container_width=True, hide_index=True, height=500)