"""
Módulo de parsing de patches
Detecta e extrai informações dos três tipos de hunks suportados
"""

import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass


@dataclass
class HunkLine:
    """Representa uma linha dentro de um hunk"""
    type: str  # ' ', '-', '+', '\'
    content: str
    line_num: Optional[int] = None


@dataclass
class Hunk:
    """Representa um hunk de patch"""
    type: str  # 'unified', 'explicit_anchor', 'implicit_anchor'
    header: str
    lines: List[HunkLine]
    
    # Para unified diff
    old_start: Optional[int] = None
    old_count: Optional[int] = None
    new_start: Optional[int] = None
    new_count: Optional[int] = None
    
    # Para âncoras
    anchor: Optional[str] = None


class PatchParser:
    """Parser para diferentes tipos de patches"""
    
    # Regex para diferentes formatos de hunk
    UNIFIED_HEADER_RE = re.compile(r'^@@\s*-(\d+)(?:,(\d+))?\s*\+(\d+)(?:,(\d+))?\s*@@(.*)$')
    EXPLICIT_ANCHOR_RE = re.compile(r'^@@\s+(.+)$')
    IMPLICIT_ANCHOR_RE = re.compile(r'^@@\s*$')
    
    def parse_patch(self, patch_content: str) -> List[Hunk]:
        """
        Parse do conteúdo do patch, retornando lista de hunks
        
        Args:
            patch_content: Conteúdo completo do patch
            
        Returns:
            Lista de objetos Hunk
        """
        lines = patch_content.splitlines()
        hunks = []
        i = 0
        
        while i < len(lines):
            line = lines[i]
            
            # Pular linhas de cabeçalho de ficheiro (--- e +++)
            if line.startswith('---') or line.startswith('+++'):
                i += 1
                continue
            
            # Procurar início de hunk
            if line.startswith('@@'):
                hunk, next_i = self._parse_hunk(lines, i)
                if hunk:
                    hunks.append(hunk)
                i = next_i
            else:
                i += 1
        
        return hunks
    
    def _parse_hunk(self, lines: List[str], start_idx: int) -> Tuple[Optional[Hunk], int]:
        """
        Parse de um único hunk a partir da posição especificada
        
        Args:
            lines: Lista de todas as linhas do patch
            start_idx: Índice da linha @@ que inicia o hunk
            
        Returns:
            Tupla (Hunk ou None, próximo índice)
        """
        if start_idx >= len(lines):
            return None, start_idx + 1
        
        header_line = lines[start_idx]
        
        # Detectar tipo de hunk
        unified_match = self.UNIFIED_HEADER_RE.match(header_line)
        explicit_anchor_match = self.EXPLICIT_ANCHOR_RE.match(header_line)
        implicit_anchor_match = self.IMPLICIT_ANCHOR_RE.match(header_line)
        
        if unified_match:
            return self._parse_unified_hunk(lines, start_idx, unified_match)
        elif explicit_anchor_match:
            return self._parse_explicit_anchor_hunk(lines, start_idx, explicit_anchor_match)
        elif implicit_anchor_match:
            return self._parse_implicit_anchor_hunk(lines, start_idx)
        else:
            # Heurística: se após @@ há várias linhas - seguidas de +, tratar como unified sem offsets
            hunk_lines = self._extract_hunk_lines(lines, start_idx + 1)
            if self._looks_like_unified_without_offsets(hunk_lines):
                return self._parse_unified_hunk_auto(lines, start_idx, hunk_lines)
        
        return None, start_idx + 1
    
    def _parse_unified_hunk(self, lines: List[str], start_idx: int, match) -> Tuple[Optional[Hunk], int]:
        """Parse de hunk unified diff clássico"""
        old_start = int(match.group(1))
        old_count = int(match.group(2)) if match.group(2) else 1
        new_start = int(match.group(3))
        new_count = int(match.group(4)) if match.group(4) else 1
        
        hunk_lines, next_idx = self._extract_hunk_lines(lines, start_idx + 1)
        
        hunk = Hunk(
            type='unified',
            header=lines[start_idx],
            lines=hunk_lines,
            old_start=old_start,
            old_count=old_count,
            new_start=new_start,
            new_count=new_count
        )
        
        return hunk, next_idx
    
    def _parse_explicit_anchor_hunk(self, lines: List[str], start_idx: int, match) -> Tuple[Optional[Hunk], int]:
        """Parse de hunk com âncora explícita"""
        anchor_text = match.group(1).strip()
        hunk_lines, next_idx = self._extract_hunk_lines(lines, start_idx + 1)
        
        hunk = Hunk(
            type='explicit_anchor',
            header=lines[start_idx],
            lines=hunk_lines,
            anchor=anchor_text
        )
        
        return hunk, next_idx
    
    def _parse_implicit_anchor_hunk(self, lines: List[str], start_idx: int) -> Tuple[Optional[Hunk], int]:
        """Parse de hunk com âncora implícita"""
        hunk_lines, next_idx = self._extract_hunk_lines(lines, start_idx + 1)
        
        # Extrair âncora implícita (primeiro bloco de linhas -)
        anchor_lines = []
        for hunk_line in hunk_lines:
            if hunk_line.type == '-':
                anchor_lines.append(hunk_line.content)
            elif hunk_line.type == '+':
                break  # Parar quando encontrar primeira linha +
        
        anchor = '\n'.join(anchor_lines) if anchor_lines else None
        
        hunk = Hunk(
            type='implicit_anchor',
            header=lines[start_idx],
            lines=hunk_lines,
            anchor=anchor
        )
        
        return hunk, next_idx
    
    def _parse_unified_hunk_auto(self, lines: List[str], start_idx: int, hunk_lines: List[HunkLine]) -> Tuple[Optional[Hunk], int]:
        """Parse de hunk unified sem offsets (calculados automaticamente)"""
        # Calcular offsets baseados no conteúdo
        old_count = sum(1 for line in hunk_lines if line.type in [' ', '-'])
        new_count = sum(1 for line in hunk_lines if line.type in [' ', '+'])
        
        hunk = Hunk(
            type='unified',
            header=lines[start_idx],
            lines=hunk_lines,
            old_start=1,  # Será calculado durante aplicação
            old_count=old_count,
            new_start=1,  # Será calculado durante aplicação
            new_count=new_count
        )
        
        return hunk, start_idx + 1 + len(hunk_lines)
    
    def _extract_hunk_lines(self, lines: List[str], start_idx: int) -> Tuple[List[HunkLine], int]:
        """
        Extrai linhas de um hunk até encontrar próximo @@ ou fim do ficheiro
        
        Args:
            lines: Lista de linhas
            start_idx: Índice de início
            
        Returns:
            Tupla (lista de HunkLine, próximo índice)
        """
        hunk_lines = []
        i = start_idx
        
        while i < len(lines):
            line = lines[i]
            
            # Parar se encontrar início de próximo hunk
            if line.startswith('@@'):
                break
            
            # Parar se encontrar cabeçalho de ficheiro
            if line.startswith('---') or line.startswith('+++'):
                break
            
            # Linha vazia marca fim do hunk para alguns formatos
            if not line.strip() and len(hunk_lines) > 0:
                # Verificar se próxima linha não-vazia é início de hunk
                next_non_empty = self._find_next_non_empty(lines, i + 1)
                if next_non_empty is not None and lines[next_non_empty].startswith('@@'):
                    break
            
            # Classificar tipo de linha
            if len(line) == 0:
                line_type = ' '
                content = ''
            elif line[0] in [' ', '-', '+', '\\']:
                line_type = line[0]
                content = line[1:] if len(line) > 1 else ''
            else:
                # Linha sem prefixo é tratada como contexto
                line_type = ' '
                content = line
            
            hunk_lines.append(HunkLine(type=line_type, content=content))
            i += 1
        
        return hunk_lines, i
    
    def _find_next_non_empty(self, lines: List[str], start_idx: int) -> Optional[int]:
        """Encontra próxima linha não-vazia"""
        for i in range(start_idx, len(lines)):
            if lines[i].strip():
                return i
        return None
    
    def _looks_like_unified_without_offsets(self, hunk_lines: List[HunkLine]) -> bool:
        """
        Verifica se conjunto de linhas parece unified diff sem offsets
        (várias linhas - seguidas de várias linhas +)
        """
        if len(hunk_lines) < 2:
            return False
        
        # Procurar padrão: linhas -, depois linhas +
        has_removals = any(line.type == '-' for line in hunk_lines)
        has_additions = any(line.type == '+' for line in hunk_lines)
        
        if not (has_removals and has_additions):
            return False
        
        # Verificar se existe transição clara de - para +
        in_removals = False
        found_transition = False
        
        for line in hunk_lines:
            if line.type == '-':
                in_removals = True
            elif line.type == '+' and in_removals:
                found_transition = True
                break
        
        return found_transition