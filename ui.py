"""
Módulo de interface de utilizador
Gere interações com o utilizador e apresentação de informações
Inclui suporte para correção de indentação Python
"""

from pathlib import Path
from typing import List, Optional, Dict, Any
from io_handler import IOHandler
from logger import PatchLogger


class UserInterface:
    """Classe para interface de utilizador"""
    
    # Códigos de cores ANSI
    BLUE = '\033[34m'
    GREEN = '\033[32m'
    RED = '\033[31m'
    YELLOW = '\033[33m'
    BOLD = '\033[1m'
    RESET = '\033[0m'
    CYAN = '\033[36m'
    
    def __init__(self):
        self.io_handler = IOHandler()
        self.logger = PatchLogger()
    
    def get_target_file(self) -> Optional[Path]:
        """
        Solicita ao utilizador o caminho do ficheiro-alvo
        
        Returns:
            Path do ficheiro ou None se cancelado
        """
        print(f"{self.BOLD}=== Aplicador de Patches Python ==={self.RESET}")
        print("Suporta: unified diff, âncoras explícitas e implícitas")
        print("Com correção automática de indentação Python\n")
        
        while True:
            try:
                path_input = input("Caminho do ficheiro-alvo ou diretório base (ou 'q' para sair): ").strip()
                
                if path_input.lower() in ['q', 'quit', 'exit']:
                    return None
                
                file_path = self.io_handler.validate_file_path(path_input)
                if file_path:
                    return file_path
                
                print(f"{self.RED}Por favor, insira um caminho válido.{self.RESET}\n")
                
            except KeyboardInterrupt:
                print(f"\n{self.YELLOW}Operação cancelada.{self.RESET}")
                return None
    
    def get_patch_content(self, target_dir: Path) -> Optional[str]:
        """
        Obtém conteúdo do patch (colado ou de ficheiro)
        
        Args:
            target_dir: Diretório do ficheiro-alvo para procurar .diff
            
        Returns:
            Conteúdo do patch ou None se cancelado
        """
        print(f"\n{self.BOLD}Como deseja fornecer o patch?{self.RESET}")
        print("1. Colar patch diretamente")
        print("2. Selecionar ficheiro .diff")
        
        while True:
            try:
                choice = input("\nEscolha (1/2 ou 'q' para sair): ").strip()
                
                if choice.lower() in ['q', 'quit', 'exit']:
                    return None
                
                if choice == '1':
                    return self._get_pasted_patch()
                elif choice == '2':
                    return self._get_patch_from_file(target_dir)
                else:
                    print(f"{self.RED}Escolha inválida. Use 1, 2 ou 'q'.{self.RESET}")
                    
            except KeyboardInterrupt:
                print(f"\n{self.YELLOW}Operação cancelada.{self.RESET}")
                return None
    
    def _get_pasted_patch(self) -> Optional[str]:
        """Obtém patch colado pelo utilizador"""
        print(f"\n{self.BOLD}Cole o patch abaixo (termine com 'END' numa linha separada):{self.RESET}")
        
        try:
            patch_content = self.io_handler.read_patch_from_stdin()
            
            if not patch_content.strip():
                print(f"{self.RED}Patch vazio fornecido.{self.RESET}")
                return None
            
            return patch_content
            
        except KeyboardInterrupt:
            print(f"\n{self.YELLOW}Entrada de patch cancelada.{self.RESET}")
            return None
    
    def _get_patch_from_file(self, target_dir: Path) -> Optional[str]:
        """Obtém patch de ficheiro .diff"""
        diff_files = self.io_handler.list_diff_files(target_dir)
        
        if not diff_files:
            print(f"{self.YELLOW}Nenhum ficheiro .diff encontrado em: {target_dir}{self.RESET}")
            return None
        
        print(f"\n{self.BOLD}Ficheiros .diff encontrados:{self.RESET}")
        for i, diff_file in enumerate(diff_files, 1):
            print(f"{i}. {diff_file.name}")
        
        while True:
            try:
                choice = input(f"\nEscolha o ficheiro (1-{len(diff_files)} ou 'q' para voltar): ").strip()
                
                if choice.lower() in ['q', 'quit', 'back']:
                    return None
                
                try:
                    index = int(choice) - 1
                    if 0 <= index < len(diff_files):
                        selected_file = diff_files[index]
                        patch_content = self.io_handler.read_patch_file(selected_file)
                        
                        if patch_content is None:
                            print(f"{self.RED}Erro ao ler o ficheiro selecionado.{self.RESET}")
                            continue
                        
                        print(f"{self.GREEN}Ficheiro carregado: {selected_file.name}{self.RESET}")
                        return patch_content
                    else:
                        print(f"{self.RED}Número inválido. Escolha entre 1 e {len(diff_files)}.{self.RESET}")
                except ValueError:
                    print(f"{self.RED}Por favor, insira um número válido.{self.RESET}")
                    
            except KeyboardInterrupt:
                print(f"\n{self.YELLOW}Seleção cancelada.{self.RESET}")
                return None
    
    def disambiguate_anchor(self, content: List[str], anchor: str, matches: List[int], context_lines: int) -> Optional[int]:
        """
        Solicita desambiguação quando há múltiplas ocorrências de âncora
        
        Args:
            content: Conteúdo do ficheiro
            anchor: Texto da âncora
            matches: Lista de índices onde a âncora foi encontrada
            context_lines: Número de linhas de contexto a mostrar
            
        Returns:
            Índice escolhido ou None se cancelado
        """
        print(f"\n{self.YELLOW}Múltiplas ocorrências encontradas para a âncora:{self.RESET}")
        print(f"{self.BLUE}{anchor}{self.RESET}\n")
        
        # Mostrar opções com contexto
        for i, match_idx in enumerate(matches, 1):
            print(f"{self.BOLD}Opção {i} (linha {match_idx + 1}):{self.RESET}")
            
            # Calcular contexto
            start_ctx = max(0, match_idx - context_lines)
            end_ctx = min(len(content), match_idx + context_lines + 1)
            
            for line_idx in range(start_ctx, end_ctx):
                line_num = line_idx + 1
                line_content = content[line_idx].rstrip('\n')
                
                # Destacar a linha da âncora
                if line_idx == match_idx:
                    print(f"  {self.BLUE}{line_num:4d}: {line_content}{self.RESET}")
                else:
                    print(f"  {line_num:4d}: {line_content}")
            
            print()  # Linha em branco entre opções
        
        # Solicitar escolha
        while True:
            try:
                choice = input(f"Escolha a ocorrência (1-{len(matches)}, 's' para pular, 'q' para cancelar): ").strip().lower()
                
                if choice in ['q', 'quit', 'cancel']:
                    return None
                elif choice in ['s', 'skip']:
                    print(f"{self.YELLOW}Hunk pulado pelo utilizador.{self.RESET}")
                    return None
                
                try:
                    index = int(choice) - 1
                    if 0 <= index < len(matches):
                        selected_line = matches[index]
                        self.logger.log_event("DISAMBIGUATION", f"Escolhida linha {selected_line + 1} para âncora: {anchor[:50]}")
                        return selected_line
                    else:
                        print(f"{self.RED}Número inválido. Escolha entre 1 e {len(matches)}.{self.RESET}")
                except ValueError:
                    print(f"{self.RED}Entrada inválida. Use um número, 's' ou 'q'.{self.RESET}")
                    
            except KeyboardInterrupt:
                print(f"\n{self.YELLOW}Desambiguação cancelada.{self.RESET}")
                return None
    
    def confirm_indentation_fix(self) -> bool:
        """
        Confirma se deve corrigir problemas de indentação
        
        Returns:
            True se deve corrigir, False caso contrário
        """
        while True:
            try:
                response = input(f"{self.YELLOW}Corrigir problemas de indentação? (s/n): {self.RESET}").strip().lower()
                
                if response in ['s', 'sim', 'y', 'yes']:
                    return True
                elif response in ['n', 'não', 'nao', 'no']:
                    return False
                else:
                    print(f"{self.RED}Por favor, responda 's' para sim ou 'n' para não{self.RESET}")
                    
            except KeyboardInterrupt:
                print(f"\n{self.YELLOW}Assumindo 'não' (correção ignorada).{self.RESET}")
                return False
    
    def show_indentation_analysis(self, analysis: dict):
        """
        Mostra análise detalhada de problemas de indentação
        
        Args:
            analysis: Dicionário com análise de indentação
        """
        print(f"\n{self.CYAN}=== ANÁLISE DE INDENTAÇÃO ==={self.RESET}")
        
        if analysis['has_tabs'] and analysis['has_spaces']:
            print(f"{self.YELLOW}⚠️  Indentação mista detectada (tabs e espaços){self.RESET}")
        elif analysis['has_tabs']:
            print(f"{self.BLUE}📋 Usando tabs para indentação{self.RESET}")
        elif analysis['has_spaces']:
            print(f"{self.BLUE}📏 Usando espaços para indentação{self.RESET}")
        
        if analysis['mixed_lines']:
            count = len(analysis['mixed_lines'])
            print(f"{self.RED}❌ {count} linha(s) com mistura de tabs e espaços{self.RESET}")
            if count <= 5:  # Mostrar linhas específicas se poucas
                lines_str = ', '.join(map(str, analysis['mixed_lines']))
                print(f"   Linhas: {lines_str}")
        
        if analysis['inconsistent_spacing']:
            print(f"{self.YELLOW}⚠️  Tamanhos de indentação inconsistentes:{self.RESET}")
            for size in analysis['inconsistent_spacing']:
                print(f"   • {size} espaços")
        
        if not (analysis['has_tabs'] and analysis['has_spaces']) and not analysis['mixed_lines'] and not analysis['inconsistent_spacing']:
            print(f"{self.GREEN}✅ Indentação consistente{self.RESET}")
        
        print(f"{self.BLUE}📊 {analysis['indented_lines']} linhas indentadas de {analysis['total_lines']} total{self.RESET}")
        print(f"{self.CYAN}{'=' * 35}{self.RESET}")
    
    def show_summary(self, results: Dict[str, Any], indentation_warnings: List[str] = None) -> None:
        """
        Mostra resumo das operações realizadas
        
        Args:
            results: Dicionário com resultados da aplicação
            indentation_warnings: Lista de avisos da correção de indentação
        """
        print(f"\n{self.CYAN}=== RESUMO DAS OPERAÇÕES ==={self.RESET}")
        
        # Estatísticas de patches
        applied = results.get('applied', 0)
        skipped = results.get('skipped', 0)
        failed = results.get('failed', 0)
        warnings = results.get('warnings', [])
        
        total_hunks = applied + skipped + failed
        success_rate = (applied / total_hunks * 100) if total_hunks > 0 else 0
        
        print(f"{self.GREEN}✓ Aplicados:{self.RESET} {applied}")
        print(f"{self.YELLOW}⚠ Ignorados:{self.RESET} {skipped}")
        print(f"{self.RED}✗ Falhados:{self.RESET} {failed}")
        print(f"{self.BLUE}📊 Taxa de sucesso:{self.RESET} {success_rate:.1f}%")
        
        # Avisos de patches
        if warnings:
            print(f"\n{self.YELLOW}Avisos de patches:{self.RESET}")
            for warning in warnings:
                print(f"  • {warning}")
        
        # Correções de indentação
        if indentation_warnings:
            print(f"\n{self.BLUE}🐍 Correções de indentação:{self.RESET}")
            for warning in indentation_warnings:
                if "AVISO:" in warning:
                    print(f"  {self.RED}• {warning}{self.RESET}")
                elif any(word in warning.lower() for word in ["convertendo", "ajustando"]):
                    print(f"  {self.YELLOW}• {warning}{self.RESET}")
                else:
                    print(f"  {self.GREEN}• {warning}{self.RESET}")
        
        print(f"{self.CYAN}{'=' * 30}{self.RESET}")
    
    def confirm_save(self) -> bool:
        """
        Solicita confirmação para gravar alterações
        
        Returns:
            True se deve gravar, False caso contrário
        """
        while True:
            try:
                choice = input(f"{self.BOLD}Gravar alterações? (s/n): {self.RESET}").strip().lower()
                
                if choice in ['s', 'sim', 'y', 'yes']:
                    return True
                elif choice in ['n', 'não', 'nao', 'no']:
                    return False
                else:
                    print(f"{self.RED}Por favor, responda 's' (sim) ou 'n' (não).{self.RESET}")
                    
            except KeyboardInterrupt:
                print(f"\n{self.YELLOW}Assumindo 'não' (alterações não gravadas).{self.RESET}")
                return False
    
    def show_success(self, message: str) -> None:
        """Mostra mensagem de sucesso"""
        print(f"{self.GREEN}✓ {message}{self.RESET}")
    
    def show_error(self, message: str) -> None:
        """Mostra mensagem de erro"""
        print(f"{self.RED}✗ {message}{self.RESET}")
    
    def show_warning(self, message: str) -> None:
        """Mostra mensagem de aviso"""
        print(f"{self.YELLOW}⚠ {message}{self.RESET}")
    
    def show_info(self, message: str) -> None:
        """Mostra mensagem informativa"""
        print(f"{self.BLUE}ℹ {message}{self.RESET}")