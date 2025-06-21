#!/usr/bin/env python3
"""
Corretor de Indentação Python
Módulo para corrigir automaticamente problemas de indentação em ficheiros Python
"""

import ast
import re
import tokenize
from io import StringIO
from pathlib import Path
from typing import List, Tuple, Optional, Dict


class IndentationCorrector:
    """Corretor de indentação para ficheiros Python"""
    
    def __init__(self, tab_size: int = 4, use_spaces: bool = True):
        """
        Inicializa o corretor de indentação
        
        Args:
            tab_size: Número de espaços por nível de indentação
            use_spaces: Se True usa espaços, se False usa tabs
        """
        self.tab_size = tab_size
        self.use_spaces = use_spaces
        self.indent_unit = ' ' * tab_size if use_spaces else '\t'
        
    def is_python_file(self, file_path: Path) -> bool:
        """
        Verifica se o ficheiro é Python
        
        Args:
            file_path: Caminho do ficheiro
            
        Returns:
            True se for ficheiro Python
        """
        if not file_path.exists():
            return False
            
        # Verificar extensão
        if file_path.suffix.lower() in ['.py', '.pyw']:
            return True
            
        # Verificar shebang para ficheiros sem extensão
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                first_line = f.readline().strip()
                if first_line.startswith('#!') and 'python' in first_line.lower():
                    return True
        except (UnicodeDecodeError, IOError):
            pass
            
        return False
    
    def detect_current_indentation(self, content: str) -> Tuple[bool, int]:
        """
        Detecta o estilo de indentação atual do código
        
        Args:
            content: Conteúdo do ficheiro
            
        Returns:
            Tupla (usa_espaços, tamanho_indentação)
        """
        space_indents = []
        tab_count = 0
        
        lines = content.split('\n')
        
        for line in lines:
            if not line.strip():  # Pular linhas vazias
                continue
                
            # Contar espaços no início
            leading_spaces = len(line) - len(line.lstrip(' '))
            # Verificar se há tabs
            if line.startswith('\t'):
                tab_count += 1
            elif leading_spaces > 0:
                space_indents.append(leading_spaces)
        
        # Se há mais tabs que espaços, usar tabs
        if tab_count > len(space_indents):
            return False, 1
            
        # Calcular tamanho mais comum de indentação com espaços
        if space_indents:
            # Encontrar o GCD dos tamanhos de indentação
            from math import gcd
            indent_size = space_indents[0]
            for size in space_indents[1:]:
                if size > 0:
                    indent_size = gcd(indent_size, size)
            
            # Valores comuns: 2, 4, 8
            if indent_size in [2, 4, 8]:
                return True, indent_size
            else:
                return True, 4  # Default para 4 espaços
                
        return True, 4  # Default
    
    def validate_syntax(self, content: str) -> Tuple[bool, Optional[str]]:
        """
        Valida se o código Python tem sintaxe correta
        
        Args:
            content: Conteúdo do código
            
        Returns:
            Tupla (é_válido, mensagem_erro)
        """
        try:
            ast.parse(content)
            return True, None
        except SyntaxError as e:
            return False, f"Erro de sintaxe na linha {e.lineno}: {e.msg}"
        except Exception as e:
            return False, f"Erro de validação: {str(e)}"
    
    def fix_mixed_indentation(self, content: str) -> str:
        """
        Corrige indentação mista (tabs e espaços)
        
        Args:
            content: Conteúdo original
            
        Returns:
            Conteúdo com indentação corrigida
        """
        lines = content.split('\n')
        corrected_lines = []
        
        for line in lines:
            if not line.strip():  # Preservar linhas vazias
                corrected_lines.append('')
                continue
                
            # Contar nível de indentação atual
            original_line = line
            stripped = line.lstrip()
            
            if not stripped:  # Linha só com espaços/tabs
                corrected_lines.append('')
                continue
            
            # Calcular nível de indentação
            indent_level = 0
            i = 0
            while i < len(line):
                if line[i] == ' ':
                    indent_level += 1
                elif line[i] == '\t':
                    # Tab conta como múltiplo do tab_size
                    indent_level += self.tab_size
                else:
                    break
                i += 1
            
            # Normalizar para unidades de indentação
            indent_units = indent_level // self.tab_size
            
            # Reconstruir linha com indentação correta
            new_line = self.indent_unit * indent_units + stripped
            corrected_lines.append(new_line)
        
        return '\n'.join(corrected_lines)
    
    def fix_indentation_errors(self, content: str) -> Tuple[str, List[str]]:
        """
        Corrige erros de indentação usando tokenizer
        
        Args:
            content: Conteúdo original
            
        Returns:
            Tupla (conteúdo_corrigido, lista_de_avisos)
        """
        warnings = []
        
        try:
            # Usar tokenizer para detectar problemas de indentação
            tokens = list(tokenize.generate_tokens(StringIO(content).readline))
            
            # Se chegou até aqui, a indentação está sintaticamente correta
            # Apenas normalizar estilo
            corrected = self.fix_mixed_indentation(content)
            
            # Detectar se houve mudanças
            if corrected != content:
                warnings.append("Indentação mista corrigida (tabs/espaços)")
                
            return corrected, warnings
            
        except tokenize.TokenError as e:
            warnings.append(f"Erro de tokenização: {e}")
            # Tentar correção básica mesmo assim
            return self.fix_mixed_indentation(content), warnings
        except Exception as e:
            warnings.append(f"Erro na correção de indentação: {e}")
            return content, warnings
    
    def analyze_indentation_issues(self, content: str) -> Dict[str, any]:
        """
        Analisa problemas de indentação no código
        
        Args:
            content: Conteúdo do código
            
        Returns:
            Dicionário com análise detalhada
        """
        lines = content.split('\n')
        analysis = {
            'has_tabs': False,
            'has_spaces': False,
            'mixed_lines': [],
            'inconsistent_spacing': [],
            'total_lines': len(lines),
            'indented_lines': 0
        }
        
        space_patterns = set()
        
        for i, line in enumerate(lines, 1):
            if not line.strip():
                continue
                
            analysis['indented_lines'] += 1
            
            # Detectar tabs
            if '\t' in line[:len(line) - len(line.lstrip())]:
                analysis['has_tabs'] = True
                
            # Detectar espaços
            leading_spaces = len(line) - len(line.lstrip(' '))
            if leading_spaces > 0:
                analysis['has_spaces'] = True
                space_patterns.add(leading_spaces)
                
            # Detectar mistura na mesma linha
            indent_part = line[:len(line) - len(line.lstrip())]
            if '\t' in indent_part and ' ' in indent_part:
                analysis['mixed_lines'].append(i)
        
        # Detectar padrões inconsistentes
        if len(space_patterns) > 1:
            # Verificar se os tamanhos são múltiplos consistentes
            sorted_patterns = sorted(space_patterns)
            base = sorted_patterns[0] if sorted_patterns else 4
            
            for pattern in sorted_patterns:
                if pattern % base != 0:
                    analysis['inconsistent_spacing'].append(pattern)
        
        return analysis
    
    def correct_file_indentation(self, content: str, file_path: Path) -> Tuple[str, List[str], bool]:
        """
        Corrige indentação de um ficheiro Python
        
        Args:
            content: Conteúdo original
            file_path: Caminho do ficheiro (para detecção de tipo)
            
        Returns:
            Tupla (conteúdo_corrigido, avisos, foi_modificado)
        """
        warnings = []
        
        # Verificar se é ficheiro Python
        if not self.is_python_file(file_path):
            return content, ["Ficheiro não é Python - indentação não corrigida"], False
        
        # Validar sintaxe original
        is_valid, error_msg = self.validate_syntax(content)
        if not is_valid:
            warnings.append(f"Sintaxe inválida detectada: {error_msg}")
            # Tentar correção mesmo assim, pode ajudar
        
        # Detectar estilo atual
        uses_spaces, current_size = self.detect_current_indentation(content)
        
        # Se o estilo detectado é diferente do configurado, avisar
        if uses_spaces != self.use_spaces:
            style_from = "espaços" if uses_spaces else "tabs"
            style_to = "espaços" if self.use_spaces else "tabs"
            warnings.append(f"Convertendo indentação de {style_from} para {style_to}")
        
        if uses_spaces and current_size != self.tab_size:
            warnings.append(f"Ajustando tamanho de indentação de {current_size} para {self.tab_size}")
        
        # Aplicar correções
        corrected_content, fix_warnings = self.fix_indentation_errors(content)
        warnings.extend(fix_warnings)
        
        # Verificar se houve mudanças
        was_modified = corrected_content != content
        
        # Validar sintaxe final
        if was_modified:
            is_valid_final, error_final = self.validate_syntax(corrected_content)
            if not is_valid_final:
                warnings.append(f"AVISO: Correção pode ter introduzido erros: {error_final}")
                # Em caso de erro, retornar original
                return content, warnings + ["Correção revertida devido a erros"], False
        
        return corrected_content, warnings, was_modified
    
    def get_correction_summary(self, analysis: Dict[str, any]) -> str:
        """
        Gera resumo da análise de indentação
        
        Args:
            analysis: Resultado da análise
            
        Returns:
            String com resumo formatado
        """
        summary = []
        
        if analysis['has_tabs'] and analysis['has_spaces']:
            summary.append("⚠️  Indentação mista detectada (tabs e espaços)")
            
        if analysis['mixed_lines']:
            count = len(analysis['mixed_lines'])
            summary.append(f"⚠️  {count} linha(s) com mistura de tabs e espaços")
            
        if analysis['inconsistent_spacing']:
            summary.append("⚠️  Tamanhos de indentação inconsistentes")
            
        if not summary:
            summary.append("✅ Indentação consistente")
            
        summary.append(f"📊 {analysis['indented_lines']} linhas indentadas de {analysis['total_lines']} total")
        
        return '\n'.join(summary)