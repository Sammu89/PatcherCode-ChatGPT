#!/usr/bin/env python3
"""
Aplicador de Patches Python - Módulo Principal
Suporta patches unified diff clássicos, âncoras explícitas e implícitas
Com correção automática de indentação para ficheiros Python
"""

import sys
import argparse
from pathlib import Path

from io_handler import IOHandler
from parser_handler import PatchParser
from applier import PatchApplier
from ui import UserInterface
from logger import PatchLogger
from indentation_corrector import IndentationCorrector


class PatchApplication:
    """Classe principal para orquestrar a aplicação de patches"""
    
    def __init__(self, context_lines=3, revert=False, fix_indentation=True, tab_size=4, use_spaces=True):
        self.context_lines = context_lines
        self.revert = revert
        self.fix_indentation = fix_indentation
        self.io_handler = IOHandler()
        self.parser = PatchParser()
        self.applier = PatchApplier(context_lines=context_lines, revert=revert)
        self.ui = UserInterface()
        self.logger = PatchLogger()
        self.indentation_corrector = IndentationCorrector(tab_size=tab_size, use_spaces=use_spaces)
        
    def run(self):
        """Executa o fluxo principal da aplicação"""
        try:
            # 1. Leitura do ficheiro-alvo
            target_file = self.ui.get_target_file()
            if not target_file:
                return 1
                
            original_content = self.io_handler.read_target_file(target_file)
            if original_content is None:
                self.ui.show_error(f"Erro ao ler o ficheiro: {target_file}")
                return 1
                
            self.logger.log_event("FILE_READ", f"Ficheiro lido: {target_file}")
            
            # 2. Leitura do patch
            patch_content = self.ui.get_patch_content(target_file.parent)
            if not patch_content:
                return 1
                
            # 3. Parsing dos hunks
            hunks = self.parser.parse_patch(patch_content)
            if not hunks:
                self.ui.show_error("Nenhum hunk válido encontrado no patch")
                return 1
                
            self.logger.log_event("PATCH_PARSED", f"Encontrados {len(hunks)} hunks")
            
            # 4. Aplicação dos hunks
            modified_content, results = self.applier.apply_hunks(
                original_content, hunks, self.ui
            )
            
            # 5. Correção de indentação (se habilitada e há mudanças)
            indentation_warnings = []
            if self.fix_indentation and results['applied'] > 0:
                if self.indentation_corrector.is_python_file(target_file):
                    self.ui.show_info("🐍 Ficheiro Python detectado - verificando indentação...")
                    
                    # Analisar problemas de indentação
                    analysis = self.indentation_corrector.analyze_indentation_issues(modified_content)
                    analysis_summary = self.indentation_corrector.get_correction_summary(analysis)
                    
                    if analysis['has_tabs'] and analysis['has_spaces'] or analysis['mixed_lines'] or analysis['inconsistent_spacing']:
                        self.ui.show_info("Problemas de indentação detectados:")
                        print(analysis_summary)
                        
                        if self.ui.confirm_indentation_fix():
                            corrected_content, warnings, was_modified = self.indentation_corrector.correct_file_indentation(
                                modified_content, target_file
                            )
                            
                            if was_modified:
                                modified_content = corrected_content
                                indentation_warnings = warnings
                                self.ui.show_success("✅ Indentação corrigida")
                                self.logger.log_event("INDENTATION_CORRECTED", f"Avisos: {'; '.join(warnings)}")
                            else:
                                self.ui.show_info("Nenhuma correção de indentação necessária")
                        else:
                            self.ui.show_info("Correção de indentação ignorada")
                    else:
                        self.ui.show_success("✅ Indentação já está consistente")
                        self.logger.log_event("INDENTATION_CHECK", "Indentação consistente")
            
            # 6. Resumo das operações
            self.ui.show_summary(results, indentation_warnings)
            
            # 7. Confirmação final
            if results['applied'] > 0:
                if self.ui.confirm_save():
                    # Criar backup e salvar
                    backup_path = self.io_handler.create_backup(target_file)
                    if backup_path:
                        self.logger.log_event("BACKUP_CREATED", str(backup_path))
                        
                    if self.io_handler.write_target_file(target_file, modified_content):
                        self.ui.show_success(f"Ficheiro atualizado: {target_file}")
                        self.logger.log_event("FILE_SAVED", str(target_file))
                    else:
                        self.ui.show_error("Erro ao gravar o ficheiro")
                        return 1
                else:
                    self.ui.show_info("Alterações descartadas")
                    self.logger.log_event("CHANGES_DISCARDED", "")
            else:
                self.ui.show_info("Nenhuma alteração foi aplicada")
                
            return 0
            
        except KeyboardInterrupt:
            self.ui.show_info("\nOperação cancelada pelo utilizador")
            return 1
        except Exception as e:
            self.ui.show_error(f"Erro inesperado: {e}")
            self.logger.log_event("ERROR", str(e))
            return 1


def parse_arguments():
    """Parse dos argumentos da linha de comandos"""
    parser = argparse.ArgumentParser(
        description="Aplicador de patches Python - Suporta unified diff, âncoras explícitas e implícitas",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:
  python main.py                              # Modo interativo padrão
  python main.py --context 5                  # Usar 5 linhas de contexto
  python main.py --revert                     # Reverter patches
  python main.py --no-indent-fix              # Desabilitar correção de indentação
  python main.py --tab-size 2 --use-tabs      # Usar tabs com tamanho 2
  
Tipos de patch suportados:
  1. Unified diff clássico: @@ -x,y +u,v @@
  2. Âncora explícita: @@ <texto_âncora>
  3. Âncora implícita: @@ (usa primeiro bloco - como âncora)

Correção de indentação:
  - Detecta automaticamente ficheiros Python (.py, .pyw, shebang)
  - Corrige mistura de tabs e espaços
  - Normaliza tamanho de indentação
  - Valida sintaxe antes e depois da correção
        """
    )
    
    parser.add_argument(
        '--context', '-c',
        type=int,
        default=3,
        help='Número de linhas de contexto para desambiguação (padrão: 3)'
    )
    
    parser.add_argument(
        '--revert', '-r',
        action='store_true',
        help='Reverter patches (inverter adições e remoções)'
    )
    
    parser.add_argument(
        '--no-indent-fix',
        action='store_true',
        help='Desabilitar correção automática de indentação'
    )
    
    parser.add_argument(
        '--tab-size',
        type=int,
        default=4,
        help='Tamanho da indentação em espaços (padrão: 4)'
    )
    
    parser.add_argument(
        '--use-tabs',
        action='store_true',
        help='Usar tabs em vez de espaços para indentação'
    )
    
    return parser.parse_args()


def main():
    """Função principal"""
    args = parse_arguments()
    
    app = PatchApplication(
        context_lines=args.context,
        revert=args.revert,
        fix_indentation=not args.no_indent_fix,
        tab_size=args.tab_size,
        use_spaces=not args.use_tabs
    )
    
    return app.run()


if __name__ == "__main__":
    sys.exit(main())