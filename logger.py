"""
Módulo de logging para o aplicador de patches
Registra eventos detalhados com timestamps
"""

import os
from datetime import datetime
from pathlib import Path
from typing import Optional


class PatchLogger:
    """Classe para logging de eventos do aplicador de patches"""
    
    def __init__(self, log_file: Optional[str] = None):
        """
        Inicializa o logger
        
        Args:
            log_file: Caminho para ficheiro de log (None para auto-gerar)
        """
        if log_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_file = f"patch_applier_{timestamp}.log"
        
        self.log_file = Path(log_file)
        self.session_start = datetime.now()
        
        # Criar directório se não existir
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Inicializar log com cabeçalho
        self._write_header()
    
    def _write_header(self) -> None:
        """Escreve cabeçalho do log"""
        try:
            with open(self.log_file, 'w', encoding='utf-8') as f:
                f.write("=" * 80 + "\n")
                f.write("PATCH APPLIER LOG\n")
                f.write("=" * 80 + "\n")
                f.write(f"Session started: {self.session_start.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Working directory: {os.getcwd()}\n")
                f.write(f"Log file: {self.log_file.absolute()}\n")
                f.write("=" * 80 + "\n\n")
        except Exception as e:
            print(f"Warning: Could not initialize log file: {e}")
    
    def log_event(self, event_type: str, message: str, details: Optional[str] = None) -> None:
        """
        Regista um evento no log
        
        Args:
            event_type: Tipo do evento (FILE_READ, HUNK_APPLIED, etc.)
            message: Mensagem principal
            details: Detalhes adicionais opcionais
        """
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(f"[{timestamp}] {event_type}: {message}\n")
                
                if details:
                    # Indentar detalhes
                    detail_lines = details.split('\n')
                    for line in detail_lines:
                        f.write(f"    {line}\n")
                
                f.write("\n")  # Linha em branco entre eventos
                
        except Exception as e:
            print(f"Warning: Could not write to log file: {e}")
    
    def log_hunk_details(self, hunk_num: int, hunk_type: str, status: str, 
                        position: Optional[int] = None, anchor: Optional[str] = None) -> None:
        """
        Regista detalhes específicos de um hunk
        
        Args:
            hunk_num: Número do hunk
            hunk_type: Tipo do hunk (unified, explicit_anchor, implicit_anchor)
            status: Status da aplicação (APPLIED, FAILED, SKIPPED)
            position: Posição no ficheiro (linha)
            anchor: Texto da âncora (se aplicável)
        """
        details = []
        details.append(f"Hunk #{hunk_num}")
        details.append(f"Type: {hunk_type}")
        details.append(f"Status: {status}")
        
        if position is not None:
            details.append(f"Position: line {position + 1}")
        
        if anchor:
            # Truncar âncora se muito longa
            anchor_preview = anchor[:100] + "..." if len(anchor) > 100 else anchor
            details.append(f"Anchor: {repr(anchor_preview)}")
        
        self.log_event("HUNK_PROCESSED", f"Hunk {hunk_num} - {status}", "\n".join(details))
    
    def log_user_choice(self, choice_type: str, choice: str, context: Optional[str] = None) -> None:
        """
        Regista escolha do utilizador
        
        Args:
            choice_type: Tipo de escolha (DISAMBIGUATION, SAVE_CONFIRM, etc.)
            choice: Escolha feita
            context: Contexto adicional
        """
        message = f"User choice: {choice}"
        details = f"Choice type: {choice_type}"
        
        if context:
            details += f"\nContext: {context}"
        
        self.log_event("USER_INTERACTION", message, details)
    
    def log_file_operation(self, operation: str, file_path: str, success: bool, 
                          details: Optional[str] = None) -> None:
        """
        Regista operação de ficheiro
        
        Args:
            operation: Tipo de operação (READ, WRITE, BACKUP)
            file_path: Caminho do ficheiro
            success: Se a operação foi bem-sucedida
            details: Detalhes adicionais
        """
        status = "SUCCESS" if success else "FAILED"
        message = f"{operation} {file_path} - {status}"
        
        self.log_event("FILE_OPERATION", message, details)
    
    def log_patch_summary(self, total_hunks: int, applied: int, failed: int, 
                         warnings: list) -> None:
        """
        Regista resumo da aplicação do patch
        
        Args:
            total_hunks: Total de hunks no patch
            applied: Hunks aplicados com sucesso
            failed: Hunks que falharam
            warnings: Lista de avisos
        """
        details = []
        details.append(f"Total hunks: {total_hunks}")
        details.append(f"Applied successfully: {applied}")
        details.append(f"Failed: {failed}")
        details.append(f"Success rate: {(applied/total_hunks*100):.1f}%" if total_hunks > 0 else "N/A")
        
        if warnings:
            details.append("\nWarnings:")
            for i, warning in enumerate(warnings, 1):
                details.append(f"  {i}. {warning}")
        
        self.log_event("PATCH_SUMMARY", f"Patch application completed", "\n".join(details))
    
    def log_error(self, error_type: str, error_message: str, traceback: Optional[str] = None) -> None:
        """
        Regista erro
        
        Args:
            error_type: Tipo do erro
            error_message: Mensagem de erro
            traceback: Traceback completo (opcional)
        """
        details = f"Error type: {error_type}\nMessage: {error_message}"
        
        if traceback:
            details += f"\nTraceback:\n{traceback}"
        
        self.log_event("ERROR", f"{error_type}: {error_message}", details)
    
    def finalize_log(self) -> None:
        """Finaliza o log com informações de sessão"""
        session_end = datetime.now()
        duration = session_end - self.session_start
        
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write("=" * 80 + "\n")
                f.write("SESSION ENDED\n")
                f.write("=" * 80 + "\n")
                f.write(f"End time: {session_end.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Duration: {duration}\n")
                f.write("=" * 80 + "\n")
                
        except Exception as e:
            print(f"Warning: Could not finalize log file: {e}")
    
    def get_log_path(self) -> Path:
        """Retorna caminho do ficheiro de log"""
        return self.log_file
    
    def __del__(self):
        """Destructor - finaliza log quando objeto é destruído"""
        try:
            self.finalize_log()
        except:
            pass  # Ignorar erros no destructor