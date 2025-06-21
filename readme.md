# Aplicador de Patches Python

Um aplicador de patches modular em Python que suporta três tipos diferentes de patches:

1. **Unified diff clássico** (`diff -u`) - formato padrão com offsets `@@ -x,y +u,v @@`
2. **Âncora explícita** - hunks com `@@ <texto_âncora>` que define o local exato
3. **Âncora implícita** - hunks apenas com `@@` usando o primeiro bloco `-` como marcador

## Características

- **Processamento de patches mistos** - um único ficheiro `.diff` pode conter hunks de diferentes tipos
- **Desambiguação interativa** - quando há múltiplas ocorrências de âncoras, o utilizador escolhe
- **Sistema de backup automático** - cria backup antes de aplicar alterações
- **Logging detalhado** - regista todas as operações e escolhas do utilizador
- **Modo de reversão** - pode reverter patches (flag `--revert`)
- **Interface colorida** - usa códigos ANSI para melhor visualização

## Instalação

Não requer instalação - usa apenas a biblioteca padrão do Python.

```bash
git clone <repositório>
cd patch-applier
python main.py
```

## Uso

### Modo Interativo (Padrão)

```bash
python main.py
```

O programa solicitará:
1. Caminho do ficheiro-alvo
2. Patch (colado ou ficheiro .diff)
3. Desambiguação quando necessário
4. Confirmação para gravar alterações

### Opções de Linha de Comandos

```bash
python main.py --help                    # Mostra ajuda
python main.py --context 5               # Usar 5 linhas de contexto
python main.py --revert                  # Reverter patches
python main.py --context 3 --revert      # Combinar opções
```

## Tipos de Patch Suportados

### 1. Unified Diff Clássico

Formato padrão do `diff -u`:

```diff
@@ -10,3 +10,3 @@
 linha de contexto
-linha a remover
+linha a adicionar
 outra linha de contexto
```

### 2. Âncora Explícita

Especifica explicitamente onde aplicar as mudanças:

```diff
@@ def minha_funcao():
-    return "antigo"
+    return "novo"
```

### 3. Âncora Implícita

Usa o primeiro bloco de remoções como âncora:

```diff
@@
-    código antigo
-    mais código antigo
+    código novo
+    mais código novo
```

### 4. Patches Mistos

Um único ficheiro pode conter diferentes tipos:

```diff
@@ -5,2 +5,2 @@
 # Hunk unified clássico
-linha1
+nova_linha1

@@ funcao_especifica():
-    # Hunk com âncora explícita
+    # código atualizado

@@
-# Hunk com âncora implícita
+# novo código
```

## Estrutura do Projeto

```
patch-applier/
├── main.py           # Orquestrador principal
├── io_handler.py     # Gestão de I/O e ficheiros
├── parser.py         # Parsing de patches
├── applier.py        # Aplicação de hunks
├── ui.py            # Interface de utilizador
├── logger.py        # Sistema de logging
└── README.md        # Esta documentação
```

## Fluxo de Execução

1. **Leitura do ficheiro-alvo** - validação e carregamento em memória
2. **Obtenção do patch** - colagem direta ou seleção de ficheiro .diff
3. **Parsing dos hunks** - classificação e extração de informações
4. **Aplicação sequencial** - processa cada hunk, com desambiguação se necessário
5. **Resumo das operações** - mostra estatísticas e avisos
6. **Confirmação final** - gravar ou descartar alterações

## Desambiguação Interativa

Quando uma âncora tem múltiplas ocorrências:

```
Múltiplas ocorrências encontradas para a âncora:
def processo_dados():

Opção 1 (linha 15):
   12: class MinhaClasse:
   13:     def __init__(self):
   14:         pass
   15:     def processo_dados():
   16:         return self.dados
   17:         
   18: def outra_funcao():

Opção 2 (linha 45):
   42: class OutraClasse:
   43:     def metodo(self):
   44:         pass
   45:     def processo_dados():
   46:         return self.outros_dados
   47:         
   48: # Fim da classe

Escolha a ocorrência (1-2, 's' para pular, 'q' para cancelar): 1
```

## Sistema de Logging

Cada execução gera um log detalhado:

```
patch_applier_20241221_143052.log
```

O log inclui:
- Timestamp de todos os eventos
- Detalhes de cada hunk processado
- Escolhas do utilizador
- Operações de ficheiro
- Avisos e erros

## Tratamento de Erros

- **Contexto divergente** - avisa mas continua com outros hunks
- **Âncora não encontrada** - regista aviso e pula hunk
- **Erros de I/O** - trata graciosamente com mensagens claras
- **Ficheiros inexistentes** - validação antes de processar

## Exemplos de Uso

### Aplicar patch simples

```bash
python main.py
# Inserir: /caminho/para/arquivo.py
# Escolher: 1 (colar patch)
# Colar patch e terminar com 'END'
# Confirmar: s (para gravar)
```

### Usar ficheiro .diff

```bash
python main.py
# Inserir: /caminho/para/arquivo.py  
# Escolher: 2 (ficheiro .diff)
# Selecionar ficheiro da lista
# Confirmar alterações
```

### Reverter patch

```bash
python main.py --revert
# Mesmo fluxo, mas inverte operações + e -
```

## Backup Automático

Antes de gravar alterações, cria automaticamente:
```
arquivo_original.py.bak_20241221_143052
```

## Limitações

- Funciona apenas com ficheiros de texto (UTF-8)
- Não suporta patches binários
- Requer interação manual para desambiguação
- Não aplica patches com conflitos automaticamente

## Contribuição

O código está organizado em módulos independentes para facilitar manutenção e extensão:

- **main.py** - ponto de entrada e orquestração
- **io_handler.py** - todas as operações de ficheiro
- **parser.py** - lógica de parsing isolada
- **applier.py** - algoritmos de aplicação
- **ui.py** - interação com utilizador
- **logger.py** - sistema de registo

Cada módulo tem responsabilidades bem definidas e interfaces claras.