import time
import datetime
import os

time.sleep(1)
atualizou = "3"
# Obtém a data e hora atuais
data_hora_atual = datetime.datetime.now()

# Expande o diretório pessoal e específica o caminho completo para o diretório onde deseja criar o arquivo
diretorio = os.path.expanduser('~/Projects/monitor/py_files/')
nome_arquivo = atualizou + '.txt'

# Criar um arquivo vazio com esse nome
with open(nome_arquivo, 'w') as arquivo:
    pass  # 'pass' é usado aqui apenas para manter a estrutura, nenhum conteúdo é escrito no arquivo

print("ARQUIVO 3")
