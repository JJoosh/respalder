#!/usr/bin/python3
import os
import py7zr
import datetime
import logging
from tkinter import Tk, filedialog
from tqdm import tqdm
import pyfiglet
from colorama import Fore, Style, init
import signal
import sys
import ctypes
import platform
import subprocess

init(autoreset=True)

# Configuración del logger
logging.basicConfig(filename='backup.log', level=logging.INFO, 
                    format='%(asctime)s:%(levelname)s:%(message)s')

# Verificar si el script se está ejecutando con privilegios de administrador (Windows) o superusuario (Linux)
def is_admin():
    if os.name == 'nt':
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False
    else:
        return os.geteuid() == 0

# Manejador de la señal SIGINT
def signal_handler(sig, frame):
    logging.warning("Proceso de respaldo interrumpido por el usuario.")
    print(Fore.RED + "\nProceso de respaldo interrumpido. Saliendo...")
    sys.exit(0)

# Registrar el manejador para SIGINT
signal.signal(signal.SIGINT, signal_handler)

def display_banner():
    banner = pyfiglet.figlet_format("Respalder", font="slant")
    print(Fore.GREEN + banner)
    print(Fore.YELLOW + "Created by Josh")
    print(Style.RESET_ALL)

def center_window(window):
    window.update_idletasks()
    width = window.winfo_width()
    height = window.winfo_height()
    x = (window.winfo_screenwidth() // 2) - (width // 2)
    y = (window.winfo_screenheight() // 2) - (height // 2)
    window.geometry(f'{width}x{height}+{x}+{y}')

def select_backup_location():
    print(Fore.CYAN + "Seleccionando ubicación de respaldo...")
    root = Tk()
    root.withdraw()  # Ocultar la ventana principal
    root.update()
    center_window(root)
    backup_location = filedialog.askdirectory(title="Selecciona el directorio donde deseas guardar el respaldo")
    root.destroy()
    return backup_location

def should_exclude(path):
    exclude_paths_windows = [
        "C:\\Windows",
        "C:\\Program Files",
        "C:\\Program Files (x86)",
        "C:\\Windows\\Temp"
    ]
    exclude_paths_linux = [
        "/proc",
        "/sys",
        "/dev",
        "/run",
        "/var/tmp",
        "/tmp"
    ]
    exclude_paths = exclude_paths_windows if os.name == 'nt' else exclude_paths_linux
    for exclude in exclude_paths:
        if path.startswith(exclude):
            return True
    return False

def set_permissions(file_path):
    try:
        os.chmod(file_path, 0o777)
    except Exception as e:
        logging.error(f"No se pudieron establecer permisos para {file_path}: {e}")
        print(Fore.RED + f"No se pudieron establecer permisos para {file_path}: {e}")

def backup_to_7z(folder, backup_location):
    print(Fore.CYAN + "Iniciando respaldo...")
    logging.info("Iniciando respaldo...")

    # El folder absoluto que queremos respaldar
    folder = os.path.abspath(folder)

    # Nombre del archivo 7z basado en la fecha y hora actual
    current_time = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    backup_filename = os.path.join(backup_location, f'respaldo_{current_time}.7z')

    # Contar el número total de archivos para la barra de progreso
    total_files = sum([len(files) for r, d, files in os.walk(folder) if not should_exclude(r)])
    
    # Crear el archivo 7z con barra de progreso
    with py7zr.SevenZipFile(backup_filename, 'w') as archive:
        with tqdm(total=total_files, unit='file', desc='Respaldo en progreso') as pbar:
            for foldername, subfolders, filenames in os.walk(folder):
                if should_exclude(foldername):
                    continue
                for filename in filenames:
                    file_path = os.path.join(foldername, filename)
                    if os.path.isfile(file_path):  # Asegurarse de que es un archivo y no un directorio
                        set_permissions(file_path)
                        try:
                            archive.write(file_path, os.path.relpath(file_path, folder))
                        except PermissionError:
                            logging.error(f"Permiso denegado: {file_path}")
                            print(Fore.RED + f"Permiso denegado: {file_path}")
                        except KeyError as e:
                            logging.error(f"Error al respaldar {file_path}: {e}")
                            print(Fore.RED + f"Error al respaldar {file_path}: {e}")
                    pbar.update(1)

    print(Fore.GREEN + f'Respaldo completo guardado en {backup_filename}')
    logging.info(f'Respaldo completo guardado en {backup_filename}')

if __name__ == "__main__":
    if not is_admin():
        if os.name == 'nt':
            print(Fore.RED + "El script necesita ejecutarse como administrador. Solicitando permisos...")
            # Relanzar el script con permisos de administrador en Windows
            ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, __file__, None, 1)
        else:
            print(Fore.RED + "El script necesita ejecutarse como superusuario (root). Solicitando permisos...")
            # Relanzar el script con permisos de superusuario en Linux
            try:
                subprocess.check_call(['sudo', sys.executable, *sys.argv])
            except subprocess.CalledProcessError as e:
                logging.error(f"Error al solicitar permisos de superusuario: {e}")
                print(Fore.RED + f"Error al solicitar permisos de superusuario: {e}")
        sys.exit(0)
    
    display_banner()
    
    # Directorio que se desea respaldar (la raíz del sistema)
    backup_folder = 'C:\\' if os.name == 'nt' else '/'
    
    # Preguntar al usuario dónde desea guardar el respaldo
    backup_location = select_backup_location()

    if backup_location:
        backup_to_7z(backup_folder, backup_location)
    else:
        print(Fore.RED + "No se seleccionó ningún directorio. Respaldo cancelado.")
        logging.warning("No se seleccionó ningún directorio. Respaldo cancelado.")
