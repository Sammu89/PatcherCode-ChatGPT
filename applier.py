"""
Módulo de aplicação de patches
Aplica hunks de diferentes tipos ao conteúdo do ficheiro
"""

import re
from typing import List, Dict, Any, Optional, Tuple
from parser_handler import Hunk, HunkLine


class PatchApplier:
    """Classe para aplicação de patches"""
    
    def __init__(self, context_lines: int = 3, revert: bool = False):
        self.context_lines = context_lines
        self.revert = revert
    
    def apply_hunks(self, content: List[str], hunks: List[Hunk], ui) -> Tuple[List[str], Dict[str, Any]]:
        """
        Aplica lista de hunks ao conteúdo
        
        Args:
            content: Conteúdo original como lista de linhas
            hunks: Lista de hunks para aplicar
            ui: Interface de utilizador para interação
            
        Returns:
            Tupla (conteúdo modificado, resultados)
        """
        modified_content = content.copy()
        results = {
            'applied': 0,
            'failed': 0,
            'warnings': []
        }
        
        for i, hunk in enumerate(hunks):
            success = False
            
            try:
                if hunk.type == 'unified':
                    success = self._apply_unified_hunk(modified_content, hunk, results)
                elif hunk.type == 'explicit_anchor':
                    success = self._apply_explicit_anchor_hunk(modified_content, hunk, results, ui)
                elif hunk.type == 'implicit_anchor':
                    success = self._apply_implicit_anchor_hunk(modified_content, hunk, results, ui)
                
                if success:
                    results['applied'] += 1
                    ui.logger.log_event("HUNK_APPLIED", f"Hunk {i+1} ({hunk.type})")
                else:
                    results['failed'] += 1
                    ui.logger.log_event("HUNK_FAILED", f"Hunk {i+1} ({hunk.type})")
                    
            except Exception as e:
                results['failed'] += 1
                warning = f"Erro no hunk {i+1}: {e}"
                results['warnings'].append(warning)
                ui.logger.log_event("HUNK_ERROR", warning)
        
        return modified_content, results
    
    def _apply_unified_hunk(self, content: List[str], hunk: Hunk, results: Dict[str, Any]) -> bool:
        """Aplica hunk unified diff"""
        # Se não tiver offsets, tentar encontrar melhor posição
        if hunk.old_start is None or hunk.old_start <= 1:
            target_line = self._find_best_unified_position(content, hunk)
            if target_line is None:
                results['warnings'].append(f"Não foi possível encontrar posição para hunk unified")
                return False
        else:
            target_line = hunk.old_start - 1  # Converter para índice 0-based
        
        # Validar contexto
        if not self._validate_unified_context(content, hunk, target_line):
            results['warnings'].append(f"Contexto divergente no hunk unified (linha {target_line + 1})")
            return False
        
        # Aplicar mudanças
        return self._perform_unified_changes(content, hunk, target_line)
    
    def _apply_explicit_anchor_hunk(self, content: List[str], hunk: Hunk, results: Dict[str, Any], ui) -> bool:
        """Aplica hunk com âncora explícita"""
        if not hunk.anchor:
            results['warnings'].append("Hunk de âncora explícita sem âncora definida")
            return False
        
        # Encontrar todas as ocorrências da âncora
        matches = self._find_anchor_matches(content, hunk.anchor)
        
        if len(matches) == 0:
            results['warnings'].append(f"Âncora não encontrada: '{hunk.anchor}'")
            return False
        elif len(matches) == 1:
            target_line = matches[0]
        else:
            # Múltiplas ocorrências - pedir desambiguação
            target_line = ui.disambiguate_anchor(content, hunk.anchor, matches, self.context_lines)
            if target_line is None:
                results['warnings'].append("Aplicação cancelada pelo utilizador")
                return False
        
        # Aplicar mudanças na posição da âncora
        return self._perform_anchor_changes(content, hunk, target_line)
    
    def _apply_implicit_anchor_hunk(self, content: List[str], hunk: Hunk, results: Dict[str, Any], ui) -> bool:
        """Aplica hunk com âncora implícita"""
        if not hunk.anchor:
            results['warnings'].append("Hunk de âncora implícita sem âncora derivada")
            return False
        
        # Encontrar ocorrências da âncora implícita
        matches = self._find_anchor_matches(content, hunk.anchor)
        
        if len(matches) == 0:
            results['warnings'].append("Âncora implícita não encontrada")
            return False
        elif len(matches) == 1:
            target_line = matches[0]
        else:
            # Múltiplas ocorrências - pedir desambiguação
            target_line = ui.disambiguate_anchor(content, hunk.anchor, matches, self.context_lines)
            if target_line is None:
                results['warnings'].append("Aplicação cancelada pelo utilizador")
                return False
        
        # Aplicar mudanças na posição da âncora
        return self._perform_anchor_changes(content, hunk, target_line)
    
    def _find_best_unified_position(self, content: List[str], hunk: Hunk) -> Optional[int]:
        """Encontra melhor posição para aplicar hunk unified sem offsets"""
        # Extrair linhas de contexto do hunk
        context_lines = []
        for line in hunk.lines:
            if line.type == ' ':
                context_lines.append(line.content.rstrip('\n'))
        
        if not context_lines:
            # Se não há contexto, usar primeira linha de remoção
            for line in hunk.lines:
                if line.type == '-':
                    return self._find_line_in_content(content, line.content.rstrip('\n'))
            return None
        
        # Procurar sequência de contexto no conteúdo
        for i in range(len(content) - len(context_lines) + 1):
            match = True
            for j, context_line in enumerate(context_lines):
                if content[i + j].rstrip('\n') != context_line:
                    match = False
                    break
            if match:
                return i
        
        return None
    
    def _find_line_in_content(self, content: List[str], target: str) -> Optional[int]:
        """Encontra linha específica no conteúdo"""
        for i, line in enumerate(content):
            if line.rstrip('\n') == target:
                return i
        return None
    
    def _validate_unified_context(self, content: List[str], hunk: Hunk, start_line: int) -> bool:
        """Valida se o contexto do hunk unified coincide com o conteúdo"""
        content_idx = start_line
        
        for line in hunk.lines:
            if line.type == ' ':  # Linha de contexto
                if content_idx >= len(content):
                    return False
                if content[content_idx].rstrip('\n') != line.content.rstrip('\n'):
                    return False
                content_idx += 1
            elif line.type == '-':  # Linha a ser removida
                if content_idx >= len(content):
                    return False
                if content[content_idx].rstrip('\n') != line.content.rstrip('\n'):
                    return False
                content_idx += 1
        
        return True
    
    def _perform_unified_changes(self, content: List[str], hunk: Hunk, start_line: int) -> bool:
        """Executa as mudanças do hunk unified"""
        try:
            # Processar mudanças em ordem reversa para manter índices válidos
            changes = []
            content_idx = start_line
            
            # Primeiro, identificar todas as mudanças
            for line in hunk.lines:
                if line.type == ' ':  # Contexto - apenas avançar
                    content_idx += 1
                elif line.type == '-':  # Remoção
                    if not self.revert:
                        changes.append(('remove', content_idx, line.content))
                    content_idx += 1
                elif line.type == '+':  # Adição
                    if not self.revert:
                        changes.append(('add', content_idx, line.content))
                    # Não incrementar content_idx para adições
            
            # Se estiver revertendo, inverter as operações
            if self.revert:
                for line in hunk.lines:
                    if line.type == '+':  # Adição vira remoção
                        for i, content_line in enumerate(content[start_line:], start_line):
                            if content_line.rstrip('\n') == line.content.rstrip('\n'):
                                changes.append(('remove', i, line.content))
                                break
                    elif line.type == '-':  # Remoção vira adição
                        changes.append(('add', content_idx, line.content))
            
            # Aplicar mudanças em ordem reversa
            changes.sort(key=lambda x: x[1], reverse=True)
            
            for change_type, idx, line_content in changes:
                if change_type == 'remove':
                    if idx < len(content):
                        content.pop(idx)
                elif change_type == 'add':
                    # Garantir que a linha tem terminação adequada
                    if not line_content.endswith('\n') and idx < len(content):
                        line_content += '\n'
                    content.insert(idx, line_content)
            
            return True
            
        except Exception:
            return False
    
    def _find_anchor_matches(self, content: List[str], anchor: str) -> List[int]:
        """Encontra todas as ocorrências de uma âncora no conteúdo"""
        matches = []
        anchor_lines = anchor.split('\n')
        
        if len(anchor_lines) == 1:
            # Âncora de linha única
            target = anchor_lines[0].strip()
            for i, line in enumerate(content):
                if target in line.rstrip('\n'):
                    matches.append(i)
        else:
            # Âncora multilinha
            for i in range(len(content) - len(anchor_lines) + 1):
                match = True
                for j, anchor_line in enumerate(anchor_lines):
                    if anchor_line.strip() not in content[i + j].rstrip('\n'):
                        match = False
                        break
                if match:
                    matches.append(i)
        
        return matches
    
    def _perform_anchor_changes(self, content: List[str], hunk: Hunk, anchor_line: int) -> bool:
        """Executa mudanças baseadas em âncora"""
        try:
            # Separar remoções e adições
            removals = []
            additions = []
            
            for line in hunk.lines:
                if line.type == '-':
                    removals.append(line.content)
                elif line.type == '+':
                    additions.append(line.content)
            
            # Se estiver revertendo, inverter operações
            if self.revert:
                removals, additions = additions, removals
            
            # Encontrar e remover linhas especificadas
            removal_indices = []
            if removals:
                # Procurar linhas a remover a partir da âncora
                search_start = anchor_line
                search_end = min(len(content), anchor_line + len(removals) * 2)
                
                for removal in removals:
                    for i in range(search_start, search_end):
                        if i < len(content) and removal.strip() in content[i].rstrip('\n'):
                            removal_indices.append(i)
                            break
            
            # Remover linhas em ordem reversa
            for idx in sorted(removal_indices, reverse=True):
                if idx < len(content):
                    content.pop(idx)
            
            # Adicionar novas linhas na posição da âncora
            insert_pos = anchor_line
            for addition in additions:
                if not addition.endswith('\n') and insert_pos < len(content):
                    addition += '\n'
                content.insert(insert_pos, addition)
                insert_pos += 1
            
            return True
            
        except Exception:
            return False