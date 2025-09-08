#!/usr/bin/env python3
"""
Documenter.py - Generador de Estructura de Proyecto
Crea un archivo con toda la estructura de carpetas y archivos del proyecto
"""

import os
from pathlib import Path
from datetime import datetime

class ProjectStructureDocumenter:
    def __init__(self, project_root=None):
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.output_file = self.project_root / "PROJECT_STRUCTURE.txt"
        
        # Directorios a ignorar
        self.ignore_dirs = {
            '__pycache__', '.git', 'node_modules', '.vscode', '.idea', 
            'venv', 'env', '.env', 'staticfiles', 'media', '.pytest_cache',
            '.mypy_cache', '.coverage', 'htmlcov', 'dist', 'build', '.tox',
            'logs', 'tmp', 'temp'
        }
        
        # Archivos a ignorar
        self.ignore_extensions = {
            '.pyc', '.pyo', '.pyd', '.so', '.egg', '.log'
        }
        
        self.ignore_files = {
            '.DS_Store', 'Thumbs.db', '.coverage'
        }

    def should_ignore_dir(self, dir_name):
        """Determina si un directorio debe ser ignorado"""
        return dir_name in self.ignore_dirs or dir_name.startswith('.')

    def should_ignore_file(self, file_name):
        """Determina si un archivo debe ser ignorado"""
        file_path = Path(file_name)
        return (
            file_name in self.ignore_files or
            file_path.suffix in self.ignore_extensions or
            (file_name.startswith('.') and file_name not in {'.env.example', '.gitignore', '.dockerignore'})
        )

    def get_directory_structure(self, path, prefix="", is_last=True):
        """Genera la estructura de directorios en formato de árbol"""
        structure_lines = []
        
        if path == self.project_root:
            structure_lines.append(f"📁 {path.name}/")
            prefix = ""
        else:
            connector = "└── " if is_last else "├── "
            structure_lines.append(f"{prefix}{connector}📁 {path.name}/")
            prefix += "    " if is_last else "│   "

        try:
            # Obtener contenido del directorio
            items = list(path.iterdir())
            
            # Separar directorios y archivos
            directories = [item for item in items if item.is_dir() and not self.should_ignore_dir(item.name)]
            files = [item for item in items if item.is_file() and not self.should_ignore_file(item.name)]
            
            # Ordenar
            directories.sort(key=lambda x: x.name.lower())
            files.sort(key=lambda x: x.name.lower())
            
            # Mostrar archivos primero
            total_items = len(files) + len(directories)
            current_item = 0
            
            for file in files:
                current_item += 1
                is_last_item = current_item == total_items
                connector = "└── " if is_last_item else "├── "
                
                # Determinar icono según extensión
                icon = self.get_file_icon(file.suffix)
                file_size = self.get_file_size(file)
                
                structure_lines.append(f"{prefix}{connector}{icon} {file.name} {file_size}")
            
            # Luego mostrar directorios (recursivamente)
            for directory in directories:
                current_item += 1
                is_last_item = current_item == total_items
                
                subdir_structure = self.get_directory_structure(
                    directory, 
                    prefix, 
                    is_last_item
                )
                structure_lines.extend(subdir_structure)
                
        except PermissionError:
            structure_lines.append(f"{prefix}├── ❌ [Acceso denegado]")
        except Exception as e:
            structure_lines.append(f"{prefix}├── ⚠️ [Error: {str(e)}]")
            
        return structure_lines

    def get_file_icon(self, extension):
        """Retorna un icono según la extensión del archivo"""
        icons = {
            '.py': '🐍',
            '.js': '📜',
            '.html': '🌐',
            '.css': '🎨',
            '.scss': '🎨',
            '.sass': '🎨',
            '.json': '📋',
            '.xml': '📋',
            '.yml': '⚙️',
            '.yaml': '⚙️',
            '.md': '📝',
            '.txt': '📄',
            '.pdf': '📕',
            '.doc': '📘',
            '.docx': '📘',
            '.xls': '📊',
            '.xlsx': '📊',
            '.jpg': '🖼️',
            '.jpeg': '🖼️',
            '.png': '🖼️',
            '.gif': '🖼️',
            '.svg': '🖼️',
            '.mp4': '🎬',
            '.mp3': '🎵',
            '.wav': '🎵',
            '.sql': '🗄️',
            '.env': '🔧',
            '.log': '📊'
        }
        return icons.get(extension.lower(), '📄')

    def get_file_size(self, file_path):
        """Obtiene el tamaño del archivo en formato legible"""
        try:
            size = file_path.stat().st_size
            if size < 1024:
                return f"({size}B)"
            elif size < 1024 * 1024:
                return f"({size/1024:.1f}KB)"
            else:
                return f"({size/(1024*1024):.1f}MB)"
        except:
            return ""

    def generate_summary(self):
        """Genera un resumen del proyecto"""
        summary_lines = []
        total_files = 0
        total_dirs = 0
        file_types = {}
        
        for root, dirs, files in os.walk(self.project_root):
            # Filtrar directorios ignorados
            dirs[:] = [d for d in dirs if not self.should_ignore_dir(d)]
            
            total_dirs += len(dirs)
            
            for file in files:
                if not self.should_ignore_file(file):
                    total_files += 1
                    ext = Path(file).suffix.lower()
                    file_types[ext] = file_types.get(ext, 0) + 1
        
        summary_lines.append("📊 RESUMEN DEL PROYECTO")
        summary_lines.append("=" * 50)
        summary_lines.append(f"📂 Total de directorios: {total_dirs}")
        summary_lines.append(f"📄 Total de archivos: {total_files}")
        summary_lines.append(f"📅 Generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        summary_lines.append("")
        
        # Top 10 tipos de archivos más comunes
        summary_lines.append("🏆 TIPOS DE ARCHIVOS MÁS COMUNES:")
        summary_lines.append("-" * 30)
        sorted_types = sorted(file_types.items(), key=lambda x: x[1], reverse=True)
        for ext, count in sorted_types[:10]:
            ext_display = ext if ext else "(sin extensión)"
            summary_lines.append(f"  {ext_display}: {count} archivos")
        
        summary_lines.append("")
        return summary_lines

    def detect_project_type(self):
        """Detecta el tipo de proyecto basado en archivos encontrados"""
        project_indicators = []
        
        # Verificar archivos específicos
        indicators = {
            'manage.py': 'Django Project',
            'package.json': 'Node.js Project', 
            'requirements.txt': 'Python Project',
            'Dockerfile': 'Dockerized Project',
            'docker-compose.yml': 'Docker Compose Project',
            'composer.json': 'PHP Project',
            'Gemfile': 'Ruby Project',
            'pom.xml': 'Java Maven Project',
            'build.gradle': 'Java Gradle Project',
            'Cargo.toml': 'Rust Project'
        }
        
        for file, project_type in indicators.items():
            if (self.project_root / file).exists():
                project_indicators.append(project_type)
        
        return project_indicators

    def generate_documentation(self):
        """Genera la documentación completa"""
        print("🔍 Analizando estructura del proyecto...")
        
        doc_lines = []
        
        # Encabezado
        doc_lines.append("🚀 DOCUMENTACIÓN DE ESTRUCTURA DEL PROYECTO")
        doc_lines.append("=" * 60)
        doc_lines.append(f"📁 Proyecto: {self.project_root.name}")
        doc_lines.append(f"📍 Ruta: {self.project_root.absolute()}")
        
        # Detectar tipo de proyecto
        project_types = self.detect_project_type()
        if project_types:
            doc_lines.append(f"🏷️  Tipo de proyecto: {', '.join(project_types)}")
        
        doc_lines.append("")
        
        # Resumen
        summary = self.generate_summary()
        doc_lines.extend(summary)
        
        # Estructura completa
        doc_lines.append("🌲 ESTRUCTURA COMPLETA DEL PROYECTO")
        doc_lines.append("=" * 60)
        structure = self.get_directory_structure(self.project_root)
        doc_lines.extend(structure)
        
        return "\n".join(doc_lines)

    def save_documentation(self):
        """Guarda la documentación en un archivo"""
        try:
            documentation = self.generate_documentation()
            
            with open(self.output_file, 'w', encoding='utf-8') as f:
                f.write(documentation)
            
            print(f"✅ Documentación generada exitosamente!")
            print(f"📄 Archivo guardado en: {self.output_file}")
            print(f"📊 Tamaño del archivo: {self.get_file_size(self.output_file)}")
            
            return self.output_file
            
        except Exception as e:
            print(f"❌ Error al generar documentación: {e}")
            return None

def main():
    """Función principal"""
    print("📚 PROJECT STRUCTURE DOCUMENTER")
    print("=" * 40)
    
    documenter = ProjectStructureDocumenter()
    
    # Verificar si estamos en un directorio válido
    if not documenter.project_root.exists():
        print("❌ El directorio del proyecto no existe.")
        return 1
    
    # Generar documentación
    output_file = documenter.save_documentation()
    
    if output_file:
        print(f"\n🎉 ¡Proceso completado!")
        print(f"📖 Puedes revisar la estructura completa en: {output_file.name}")
        return 0
    else:
        return 1

if __name__ == "__main__":
    exit(main())