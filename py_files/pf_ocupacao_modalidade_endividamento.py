#!/usr/bin/env python
# coding: utf-8

# In[1]:


import zipfile
import os
import pandas as pd
import plotly.express as px


# In[2]:


def concatenar_csvs(diretorio):
    frames = []

    for arquivo in os.listdir(diretorio):
        if arquivo.endswith('.csv'):
            caminho_arquivo = os.path.join(diretorio, arquivo)
            
            df = pd.read_csv(caminho_arquivo, encoding='utf-8', delimiter=";", decimal=",")
            df = df.rename(columns={df.columns[0]: "data_base"})
            df['data_base'] = pd.to_datetime(df['data_base'], format="%Y-%m-%d")
            df['ocupacao']=df['ocupacao'].str.replace('PF - ','')
            df['modalidade']=df['modalidade'].str.replace('PF - ','')
            df['mes'] = df['data_base'].dt.month #cria uma nova coluna com mês
             
            #Filtros:
            df = df[df['cliente'] == 'PF']
            df = df[df['mes'] == 12]
            df = df[['data_base', 'ocupacao', 'modalidade', 'carteira_ativa']]
            
            #Agrupamentos para análise
            df = df.groupby(['data_base', 'ocupacao', 'modalidade'])['carteira_ativa'].sum().reset_index()
            
            frames.append(df)

    df_concatenado = pd.concat(frames, ignore_index=True)

    return df_concatenado


# In[3]:


anos = list(range(2012, 2024))
dataframes = []

for ano in anos:
    diretorio = f"planilha_{ano}"
    dataframe_ano = concatenar_csvs(diretorio)
    dataframes.append(dataframe_ano)

df_total = pd.concat(dataframes, ignore_index=False)


# In[4]:


df_total.head()


# In[5]:


df_total.info()


# In[7]:


import deflatebr as dbr


# In[13]:


df_total['carteira_ativa_deflacionada'] = dbr.deflate(nominal_values=df_total['carteira_ativa'], nominal_dates=df_total['data_base'], real_date='2022-12') #corrigir para 12/2022


# In[14]:


df_total.head(3)


# In[15]:


pd.set_option('display.float_format', '{:.2f}'.format)
df_total.head(3)


# In[16]:


fig = px.line(df_total, 
             x='data_base',
             y='carteira_ativa_deflacionada', 
             color='modalidade', 
             animation_frame='ocupacao')

fig.update_layout(title_text='Pessoa Física - Carteira Ativa por Modalidade de Crédito e Ocupação',
             xaxis_title='Ocupação',
             yaxis_title='Carteira Ativa',
             height=500, 
             width=800)

fig.show()


# In[18]:


df_total.to_csv("pf_ocupacao_modalidade_endividamento_final.csv")


# In[ ]:




