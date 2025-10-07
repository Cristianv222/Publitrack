#!/usr/bin/env python3
"""
Universal Project Documenter - Generador Universal de Estructura de Proyectos
Analiza y documenta la estructura de CUALQUIER tipo de proyecto
"""

import os
import sys
import argparse
from pathlib import Path
from datetime import datetime
from collections import defaultdict
import json

class UniversalProjectDocumenter:
    def __init__(self, project_root=None, output_format='txt', output_name=None):
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.output_format = output_format.lower()
        
        # Nombre del archivo de salida
        if output_name:
            self.output_file = self.project_root / output_name
        else:
            extension = 'md' if output_format == 'markdown' else output_format
            self.output_file = self.project_root / f"PROJECT_STRUCTURE.{extension}"
        
        # Directorios a ignorar (más completo)
        self.ignore_dirs = {
            # Python
            '__pycache__', '.pytest_cache', '.mypy_cache', '.tox', 'venv', 'env', '.env',
            # JavaScript/Node
            'node_modules', '.npm', '.yarn', 'bower_components',
            # Control de versiones
            '.git', '.svn', '.hg', '.bzr',
            # IDEs
            '.vscode', '.idea', '.eclipse', '.settings', '.project',
            # Build/Compilación
            'dist', 'build', 'target', 'out', 'bin', 'obj',
            # Temporales y Logs
            'tmp', 'temp', 'logs', 'log',
            # Caché
            '.cache', '.parcel-cache', '.next',
            # Testing
            'coverage', 'htmlcov', '.coverage', '.nyc_output',
            # Otros
            'staticfiles', 'media', '.sass-cache', '.gradle'
        }
        
        # Archivos a ignorar
        self.ignore_extensions = {
            '.pyc', '.pyo', '.pyd', '.so', '.dll', '.dylib', '.egg', '.egg-info',
            '.log', '.bak', '.swp', '.swo', '.tmp', '.temp', '.cache',
            '.class', '.o', '.obj', '.exe'
        }
        
        self.ignore_files = {
            '.DS_Store', 'Thumbs.db', 'desktop.ini', '.coverage', 
            'npm-debug.log', 'yarn-error.log', 'package-lock.json',
            'yarn.lock', 'poetry.lock', 'Pipfile.lock'
        }

        # Estadísticas
        self.stats = {
            'total_dirs': 0,
            'total_files': 0,
            'total_size': 0,
            'file_types': defaultdict(int),
            'largest_files': []
        }

    def should_ignore_dir(self, dir_name):
        """Determina si un directorio debe ser ignorado"""
        return dir_name in self.ignore_dirs or dir_name.startswith('.')

    def should_ignore_file(self, file_name):
        """Determina si un archivo debe ser ignorado"""
        file_path = Path(file_name)
        
        # Mantener algunos archivos de configuración importantes
        important_files = {
            '.gitignore', '.dockerignore', '.env.example', '.editorconfig',
            '.eslintrc', '.prettierrc', '.babelrc', 'Dockerfile', 'Makefile',
            'README.md', 'LICENSE', 'CHANGELOG.md'
        }
        
        if file_name in important_files:
            return False
            
        return (
            file_name in self.ignore_files or
            file_path.suffix in self.ignore_extensions or
            file_name.startswith('.')
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
            
            # Ordenar alfabéticamente
            directories.sort(key=lambda x: x.name.lower())
            files.sort(key=lambda x: x.name.lower())
            
            # Actualizar estadísticas
            self.stats['total_dirs'] += len(directories)
            
            # Mostrar archivos primero
            total_items = len(files) + len(directories)
            current_item = 0
            
            for file in files:
                current_item += 1
                is_last_item = current_item == total_items
                connector = "└── " if is_last_item else "├── "
                
                # Obtener información del archivo
                icon = self.get_file_icon(file.suffix)
                file_size = self.get_file_size_bytes(file)
                file_size_str = self.format_file_size(file_size)
                
                # Actualizar estadísticas
                self.stats['total_files'] += 1
                self.stats['total_size'] += file_size
                self.stats['file_types'][file.suffix.lower() if file.suffix else '(sin ext)'] += 1
                self.stats['largest_files'].append((file, file_size))
                
                structure_lines.append(f"{prefix}{connector}{icon} {file.name} {file_size_str}")
            
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
            # Programación
            '.py': '🐍', '.js': '📜', '.ts': '💠', '.jsx': '⚛️', '.tsx': '⚛️',
            '.java': '☕', '.cpp': '⚙️', '.c': '⚙️', '.h': '⚙️', '.hpp': '⚙️',
            '.cs': '#️⃣', '.go': '🐹', '.rs': '🦀', '.php': '🐘', '.rb': '💎',
            '.swift': '🦅', '.kt': '🎯', '.scala': '📈', '.r': '📊',
            '.dart': '🎯', '.lua': '🌙', '.perl': '🐪', '.shell': '🐚',
            '.sh': '🐚', '.bash': '🐚', '.zsh': '🐚', '.ps1': '💻',
            
            # Web
            '.html': '🌐', '.htm': '🌐', '.css': '🎨', '.scss': '🎨',
            '.sass': '🎨', '.less': '🎨', '.vue': '💚', '.svelte': '🔥',
            
            # Datos y Configuración
            '.json': '📋', '.xml': '📋', '.yaml': '⚙️', '.yml': '⚙️',
            '.toml': '⚙️', '.ini': '⚙️', '.conf': '⚙️', '.config': '⚙️',
            '.env': '🔧', '.properties': '⚙️',
            
            # Documentación
            '.md': '📝', '.markdown': '📝', '.txt': '📄', '.rst': '📝',
            '.pdf': '📕', '.doc': '📘', '.docx': '📘',
            
            # Hojas de cálculo
            '.xls': '📊', '.xlsx': '📊', '.csv': '📊',
            
            # Imágenes
            '.jpg': '🖼️', '.jpeg': '🖼️', '.png': '🖼️', '.gif': '🖼️',
            '.svg': '🖼️', '.ico': '🖼️', '.webp': '🖼️', '.bmp': '🖼️',
            
            # Audio/Video
            '.mp4': '🎬', '.avi': '🎬', '.mov': '🎬', '.mkv': '🎬',
            '.mp3': '🎵', '.wav': '🎵', '.ogg': '🎵', '.flac': '🎵',
            
            # Base de datos
            '.sql': '🗄️', '.db': '🗄️', '.sqlite': '🗄️', '.mdb': '🗄️',
            
            # Comprimidos
            '.zip': '📦', '.rar': '📦', '.7z': '📦', '.tar': '📦',
            '.gz': '📦', '.bz2': '📦',
            
            # Otros
            '.log': '📊', '.lock': '🔒', '.gitignore': '🚫',
            '.dockerignore': '🚫', 'Dockerfile': '🐳', 'Makefile': '🔨'
        }
        return icons.get(extension.lower(), '📄')

    def get_file_size_bytes(self, file_path):
        """Obtiene el tamaño del archivo en bytes"""
        try:
            return file_path.stat().st_size
        except:
            return 0

    def format_file_size(self, size):
        """Formatea el tamaño del archivo en formato legible"""
        if size < 1024:
            return f"({size}B)"
        elif size < 1024 * 1024:
            return f"({size/1024:.1f}KB)"
        elif size < 1024 * 1024 * 1024:
            return f"({size/(1024*1024):.1f}MB)"
        else:
            return f"({size/(1024*1024*1024):.2f}GB)"

    def detect_project_type(self):
        """Detecta el tipo de proyecto basado en archivos encontrados"""
        project_indicators = []
        
        # Verificar archivos específicos y sus tecnologías
        indicators = {
            # Python
            'manage.py': '🐍 Django',
            'setup.py': '🐍 Python Package',
            'pyproject.toml': '🐍 Python Modern Project',
            'requirements.txt': '🐍 Python',
            'Pipfile': '🐍 Python (Pipenv)',
            'poetry.lock': '🐍 Python (Poetry)',
            
            # JavaScript/Node
            'package.json': '📦 Node.js/JavaScript',
            'yarn.lock': '🧶 Yarn Project',
            'pnpm-lock.yaml': '📦 PNPM Project',
            'next.config.js': '▲ Next.js',
            'nuxt.config.js': '💚 Nuxt.js',
            'vue.config.js': '💚 Vue.js',
            'angular.json': '🅰️ Angular',
            'svelte.config.js': '🔥 Svelte',
            'gatsby-config.js': '⚛️ Gatsby',
            
            # Java
            'pom.xml': '☕ Java Maven',
            'build.gradle': '☕ Java Gradle',
            'build.gradle.kts': '☕ Kotlin Gradle',
            
            # PHP
            'composer.json': '🐘 PHP Composer',
            
            # Ruby
            'Gemfile': '💎 Ruby',
            'Rakefile': '💎 Ruby Rake',
            
            # Go
            'go.mod': '🐹 Go Module',
            
            # Rust
            'Cargo.toml': '🦀 Rust',
            
            # .NET
            'Program.cs': '#️⃣ .NET/C#',
            'App.config': '#️⃣ .NET',
            
            # Contenedores
            'Dockerfile': '🐳 Docker',
            'docker-compose.yml': '🐳 Docker Compose',
            'docker-compose.yaml': '🐳 Docker Compose',
            
            # CI/CD
            '.gitlab-ci.yml': '🦊 GitLab CI',
            '.travis.yml': '✅ Travis CI',
            'Jenkinsfile': '👨 Jenkins',
            
            # Otros
            'CMakeLists.txt': '⚙️ CMake C/C++',
            'Makefile': '🔨 Make Project',
            'README.md': '📖 Documented Project'
        }
        
        for file, project_type in indicators.items():
            file_path = self.project_root / file
            if file_path.exists():
                project_indicators.append(project_type)
        
        # Buscar en subdirectorios para detectar más patrones
        try:
            for root, dirs, files in os.walk(self.project_root):
                if any(ignored in root for ignored in self.ignore_dirs):
                    continue
                    
                # Detectar frameworks por estructura
                if 'src' in dirs and 'public' in dirs:
                    if 'package.json' in files:
                        project_indicators.append('⚛️ React-like Framework')
                        break
        except:
            pass
        
        return list(set(project_indicators))  # Eliminar duplicados

    def generate_summary(self):
        """Genera un resumen detallado del proyecto"""
        summary_lines = []
        
        summary_lines.append("📊 RESUMEN DEL PROYECTO")
        summary_lines.append("=" * 60)
        summary_lines.append(f"📂 Total de directorios: {self.stats['total_dirs']}")
        summary_lines.append(f"📄 Total de archivos: {self.stats['total_files']}")
        summary_lines.append(f"💾 Tamaño total: {self.format_file_size(self.stats['total_size'])}")
        summary_lines.append(f"📅 Generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        summary_lines.append("")
        
        # Top 15 tipos de archivos más comunes
        if self.stats['file_types']:
            summary_lines.append("🏆 TIPOS DE ARCHIVOS MÁS COMUNES:")
            summary_lines.append("-" * 40)
            sorted_types = sorted(self.stats['file_types'].items(), 
                                key=lambda x: x[1], reverse=True)
            for ext, count in sorted_types[:15]:
                percentage = (count / self.stats['total_files']) * 100
                summary_lines.append(f"  {ext:15} : {count:4} archivos ({percentage:5.1f}%)")
            summary_lines.append("")
        
        # Top 10 archivos más grandes
        if self.stats['largest_files']:
            summary_lines.append("📏 ARCHIVOS MÁS GRANDES:")
            summary_lines.append("-" * 40)
            largest = sorted(self.stats['largest_files'], 
                           key=lambda x: x[1], reverse=True)[:10]
            for file, size in largest:
                rel_path = file.relative_to(self.project_root)
                summary_lines.append(f"  {self.format_file_size(size):10} - {rel_path}")
            summary_lines.append("")
        
        return summary_lines

    def generate_documentation_txt(self):
        """Genera la documentación en formato TXT"""
        doc_lines = []
        
        # Encabezado
        doc_lines.append("🚀 DOCUMENTACIÓN DE ESTRUCTURA DEL PROYECTO")
        doc_lines.append("=" * 70)
        doc_lines.append(f"📁 Proyecto: {self.project_root.name}")
        doc_lines.append(f"📍 Ruta: {self.project_root.absolute()}")
        
        # Detectar tipo de proyecto
        project_types = self.detect_project_type()
        if project_types:
            doc_lines.append(f"\n🏷️  TECNOLOGÍAS DETECTADAS:")
            for tech in project_types:
                doc_lines.append(f"   • {tech}")
        
        doc_lines.append("")
        doc_lines.append("")
        
        # Resumen
        summary = self.generate_summary()
        doc_lines.extend(summary)
        
        # Estructura completa
        doc_lines.append("🌲 ESTRUCTURA COMPLETA DEL PROYECTO")
        doc_lines.append("=" * 70)
        structure = self.get_directory_structure(self.project_root)
        doc_lines.extend(structure)
        
        doc_lines.append("")
        doc_lines.append("=" * 70)
        doc_lines.append("✨ Generado por Universal Project Documenter")
        doc_lines.append("=" * 70)
        
        return "\n".join(doc_lines)

    def generate_documentation_markdown(self):
        """Genera la documentación en formato Markdown"""
        doc_lines = []
        
        # Encabezado
        doc_lines.append(f"# 🚀 {self.project_root.name}")
        doc_lines.append("")
        doc_lines.append(f"**Ruta:** `{self.project_root.absolute()}`")
        doc_lines.append("")
        doc_lines.append(f"**Generado:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        doc_lines.append("")
        
        # Tecnologías detectadas
        project_types = self.detect_project_type()
        if project_types:
            doc_lines.append("## 🏷️ Tecnologías Detectadas")
            doc_lines.append("")
            for tech in project_types:
                doc_lines.append(f"- {tech}")
            doc_lines.append("")
        
        # Resumen
        doc_lines.append("## 📊 Resumen del Proyecto")
        doc_lines.append("")
        doc_lines.append(f"| Métrica | Valor |")
        doc_lines.append(f"|---------|-------|")
        doc_lines.append(f"| 📂 Directorios | {self.stats['total_dirs']} |")
        doc_lines.append(f"| 📄 Archivos | {self.stats['total_files']} |")
        doc_lines.append(f"| 💾 Tamaño Total | {self.format_file_size(self.stats['total_size'])} |")
        doc_lines.append("")
        
        # Tipos de archivos
        if self.stats['file_types']:
            doc_lines.append("### 🏆 Tipos de Archivos")
            doc_lines.append("")
            doc_lines.append("| Extensión | Cantidad | Porcentaje |")
            doc_lines.append("|-----------|----------|------------|")
            sorted_types = sorted(self.stats['file_types'].items(), 
                                key=lambda x: x[1], reverse=True)[:10]
            for ext, count in sorted_types:
                percentage = (count / self.stats['total_files']) * 100
                doc_lines.append(f"| {ext} | {count} | {percentage:.1f}% |")
            doc_lines.append("")
        
        # Estructura
        doc_lines.append("## 🌲 Estructura del Proyecto")
        doc_lines.append("")
        doc_lines.append("```")
        structure = self.get_directory_structure(self.project_root)
        doc_lines.extend(structure)
        doc_lines.append("```")
        doc_lines.append("")
        
        doc_lines.append("---")
        doc_lines.append("*Generado por Universal Project Documenter*")
        
        return "\n".join(doc_lines)

    def generate_documentation_json(self):
        """Genera la documentación en formato JSON"""
        data = {
            'project': {
                'name': self.project_root.name,
                'path': str(self.project_root.absolute()),
                'generated_at': datetime.now().isoformat()
            },
            'technologies': self.detect_project_type(),
            'statistics': {
                'total_directories': self.stats['total_dirs'],
                'total_files': self.stats['total_files'],
                'total_size_bytes': self.stats['total_size'],
                'total_size_formatted': self.format_file_size(self.stats['total_size']),
                'file_types': dict(self.stats['file_types'])
            },
            'structure': self.get_structure_dict(self.project_root)
        }
        
        return json.dumps(data, indent=2, ensure_ascii=False)

    def get_structure_dict(self, path):
        """Genera la estructura en formato de diccionario para JSON"""
        try:
            items = list(path.iterdir())
            directories = [item for item in items if item.is_dir() and not self.should_ignore_dir(item.name)]
            files = [item for item in items if item.is_file() and not self.should_ignore_file(item.name)]
            
            structure = {
                'type': 'directory',
                'name': path.name,
                'children': []
            }
            
            # Añadir archivos
            for file in sorted(files, key=lambda x: x.name.lower()):
                structure['children'].append({
                    'type': 'file',
                    'name': file.name,
                    'size': self.get_file_size_bytes(file),
                    'extension': file.suffix
                })
            
            # Añadir directorios recursivamente
            for directory in sorted(directories, key=lambda x: x.name.lower()):
                structure['children'].append(self.get_structure_dict(directory))
            
            return structure
        except:
            return {'type': 'directory', 'name': path.name, 'error': 'Access denied'}

    def save_documentation(self):
        """Guarda la documentación en el formato especificado"""
        try:
            print(f"🔍 Analizando estructura del proyecto...")
            print(f"📁 Directorio: {self.project_root}")
            print(f"📄 Formato: {self.output_format.upper()}")
            
            # Generar documentación según formato
            if self.output_format == 'markdown' or self.output_format == 'md':
                documentation = self.generate_documentation_markdown()
            elif self.output_format == 'json':
                documentation = self.generate_documentation_json()
            else:  # txt por defecto
                documentation = self.generate_documentation_txt()
            
            # Guardar archivo
            with open(self.output_file, 'w', encoding='utf-8') as f:
                f.write(documentation)
            
            print(f"\n✅ ¡Documentación generada exitosamente!")
            print(f"📄 Archivo guardado en: {self.output_file}")
            print(f"📊 Tamaño del archivo: {self.format_file_size(self.get_file_size_bytes(self.output_file))}")
            print(f"\n📈 Estadísticas:")
            print(f"   • Directorios analizados: {self.stats['total_dirs']}")
            print(f"   • Archivos encontrados: {self.stats['total_files']}")
            print(f"   • Tamaño total: {self.format_file_size(self.stats['total_size'])}")
            
            return self.output_file
            
        except Exception as e:
            print(f"❌ Error al generar documentación: {e}")
            import traceback
            traceback.print_exc()
            return None


def main():
    """Función principal con argumentos de línea de comandos"""
    parser = argparse.ArgumentParser(
        description='📚 Universal Project Documenter - Analiza cualquier proyecto',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  %(prog)s                                    # Analiza el directorio actual
  %(prog)s /ruta/al/proyecto                  # Analiza un directorio específico
  %(prog)s -f markdown                        # Genera en formato Markdown
  %(prog)s -f json -o estructura.json         # Genera JSON con nombre personalizado
  %(prog)s /proyecto -f md -o README.md       # Analiza proyecto y guarda como README
        """
    )
    
    parser.add_argument(
        'directory',
        nargs='?',
        default='.',
        help='Directorio del proyecto a analizar (por defecto: directorio actual)'
    )
    
    parser.add_argument(
        '-f', '--format',
        choices=['txt', 'markdown', 'md', 'json'],
        default='txt',
        help='Formato de salida (por defecto: txt)'
    )
    
    parser.add_argument(
        '-o', '--output',
        help='Nombre del archivo de salida (por defecto: PROJECT_STRUCTURE.{formato})'
    )
    
    args = parser.parse_args()
    
    # Banner
    print("=" * 60)
    print("📚 UNIVERSAL PROJECT DOCUMENTER")
    print("   Analiza y documenta CUALQUIER tipo de proyecto")
    print("=" * 60)
    print()
    
    # Verificar que el directorio existe
    project_path = Path(args.directory).resolve()
    if not project_path.exists():
        print(f"❌ Error: El directorio '{project_path}' no existe.")
        return 1
    
    if not project_path.is_dir():
        print(f"❌ Error: '{project_path}' no es un directorio.")
        return 1
    
    # Crear documenter
    documenter = UniversalProjectDocumenter(
        project_root=project_path,
        output_format=args.format,
        output_name=args.output
    )
    
    # Generar documentación
    output_file = documenter.save_documentation()
    
    if output_file:
        print(f"\n🎉 ¡Proceso completado exitosamente!")
        print(f"📖 Revisa la estructura en: {output_file.name}")
        return 0
    else:
        return 1


if __name__ == "__main__":
    sys.exit(main())