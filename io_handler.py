"""

Módulo de gestão de I/O para o aplicador de patches

Responsável por leitura/escrita de ficheiros e criação de backups

"""



import os

import shutil

from pathlib import Path

from datetime import datetime

from typing import List, Optional





class IOHandler:

    """Classe para gestão de operações de I/O"""

    

    def read_target_file(self, file_path: Path) -> Optional[List[str]]:

        """

        Lê o ficheiro-alvo e retorna o conteúdo como lista de linhas

        

        Args:

            file_path: Caminho para o ficheiro

            

        Returns:

            Lista de linhas ou None em caso de erro

        """

        try:

            with open(file_path, 'r', encoding='utf-8') as f:

                # Preservar terminações de linha originais

                content = f.read()

                lines = content.splitlines(keepends=True)

                

                # Se o ficheiro não termina com newline, a última linha não terá

                if content and not content.endswith('\n'):

                    if lines:

                        lines[-1] = lines[-1].rstrip('\n')

                

                return lines

                

        except FileNotFoundError:

            print(f"Error: File not found: {file_path}")

            return None

        except PermissionError:

            print(f"Error: Permission denied: {file_path}")

            return None

        except UnicodeDecodeError:

            print(f"Error: Encoding issue in file: {file_path}")

            return None

        except Exception as e:

            print(f"Error reading file {file_path}: {e}")

            return None

    

    def write_target_file(self, file_path: Path, content: List[str]) -> bool:

        """

        Escreve o conteúdo no ficheiro-alvo

        

        Args:

            file_path: Caminho para o ficheiro

            content: Lista de linhas para escrever

            

        Returns:

            True se sucesso, False caso contrário

        """

        try:

            with open(file_path, 'w', encoding='utf-8') as f:

                for line in content:

                    f.write(line)

            return True

            

        except PermissionError:

            print(f"Error: Permission denied (write): {file_path}")

            return False

        except Exception as e:

            print(f"Error writing file {file_path}: {e}")

            return False

    

    def create_backup(self, file_path: Path) -> Optional[Path]:

        """

        Cria uma cópia de backup do ficheiro

        

        Args:

            file_path: Caminho para o ficheiro original

            

        Returns:

            Caminho do backup ou None em caso de erro

        """

        try:

            timestamp = datetime.now().strftime("%d%m%y_%H%M")

            backup_name = f"{file_path.stem}_{timestamp}.bak"

            backup_path = file_path.parent / backup_name

            

            shutil.copy2(file_path, backup_path)

            return backup_path

            

        except Exception as e:

            print(f"Warning: Could not create backup: {e}")

            return None

    

    def read_patch_from_stdin(self) -> str:

        """

        Lê patch colado pelo utilizador até encontrar 'END'

        

        Returns:

            Conteúdo do patch como string

        """

        print("Paste the patch below (finish input with Ctrl+D):")

        lines = []

        

        try:

            while True:

                line = input()

                lines.append(line)

        except EOFError:

            pass  # Ctrl+D or EOF

        except KeyboardInterrupt:

            raise

        

        return '\n'.join(lines)

    

    def list_diff_files(self, directory: Path) -> List[Path]:

        """

        Lista ficheiros .diff no diretório especificado

        

        Args:

            directory: Diretório para procurar

            

        Returns:

            Lista de caminhos para ficheiros .diff

        """

        try:

            diff_files = []

            for file_path in directory.glob('*.diff'):

                if file_path.is_file():

                    diff_files.append(file_path)

            

            # Ordenar por nome

            diff_files.sort(key=lambda x: x.name.lower())

            return diff_files

            

        except Exception as e:

            print(f"Error listing .diff files: {e}")

            return []

    

    def read_patch_file(self, patch_path: Path) -> Optional[str]:

        """

        Lê um ficheiro de patch

        

        Args:

            patch_path: Caminho para o ficheiro de patch

            

        Returns:

            Conteúdo do patch ou None em caso de erro

        """

        try:

            with open(patch_path, 'r', encoding='utf-8') as f:

                return f.read()

                

        except FileNotFoundError:

            print(f"Error: Patch file not found: {patch_path}")

            return None

        except PermissionError:

            print(f"Error: Permission denied: {patch_path}")

            return None

        except UnicodeDecodeError:

            try:

                # Tentar com outras codificações

                with open(patch_path, 'r', encoding='latin-1') as f:

                    return f.read()

            except Exception:

                print(f"Error: Encoding issue in file: {patch_path}")

                return None

        except Exception as e:

            print(f"Error reading patch {patch_path}: {e}")

            return None

    

    def validate_file_path(self, path_str: str) -> Optional[Path]:

        """

        Valida e normaliza um caminho de ficheiro

        

        Args:

            path_str: String do caminho (pode conter aspas)

            

        Returns:

            Path objeto ou None se inválido

        """

        # Remover aspas se presentes

        path_str = path_str.strip().strip('"').strip("'")

        

        if not path_str:

            return None

        

        try:

            path = Path(path_str).resolve()

            

            if not path.exists():

                print(f"Error: File does not exist: {path}")

                return None

            

            if path.is_dir():

                return path

            if not path.is_file():

                print(f"Error: Path is not a valid file or directory: {path}")

                return None

            

            return path

            

        except Exception as e:

            print(f"Error: Invalid path '{path_str}': {e}")

            return None