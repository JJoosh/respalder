#!/usr/bin/python3
import os
import py7zr
import datetime
from tkinter import Tk, filedialog
from tqdm import tqdm
import pyfiglet
from colorama import Fore, Style, init
import signal
import sys
import ctypes

init(autoreset=True)

# Verificar si el script se está ejecutando con privilegios de administrador
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

# Manejador de la señal SIGINT
def signal_handler(sig, frame):
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

def backup_to_7z(folder, backup_location):
    print(Fore.CYAN + "Iniciando respaldo...")
    # El folder absoluto que queremos respaldar
    folder = os.path.abspath(folder)

    # Nombre del archivo 7z basado en la fecha y hora actual
    current_time = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    backup_filename = os.path.join(backup_location, f'respaldo_{current_time}.7z')

    # Contar el número total de archivos para la barra de progreso
    total_files = sum([len(files) for r, d, files in os.walk(folder)])
    
    # Crear el archivo 7z con barra de progreso
    with py7zr.SevenZipFile(backup_filename, 'w') as archive:
        with tqdm(total=total_files, unit='file', desc='Respaldo en progreso') as pbar:
            for foldername, subfolders, filenames in os.walk(folder):
                for filename in filenames:
                    file_path = os.path.join(foldername, filename)
                    if os.path.isfile(file_path):  # Asegurarse de que es un archivo y no un directorio
                        try:
                            archive.write(file_path, os.path.relpath(file_path, folder))
                        except PermissionError:
                            print(Fore.RED + f"Permiso denegado: {file_path}")
                        except KeyError as e:
                            print(Fore.RED + f"Error al respaldar {file_path}: {e}")
                    pbar.update(1)

    print(Fore.GREEN + f'Respaldo completo guardado en {backup_filename}')

if __name__ == "__main__":
    if not is_admin():
        print(Fore.RED + "El script necesita ejecutarse como administrador. Solicitando permisos...")
        # Relanzar el script con permisos de administrador
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, __file__, None, 1)
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
