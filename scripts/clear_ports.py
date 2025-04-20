import socket
import subprocess
from typing import List

def get_used_ports() -> List[int]:
    """Получить список используемых портов в системе"""
    used_ports = []
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        for port in range(1, 65536):
            try:
                s.bind(('0.0.0.0', port))
                s.close()
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            except OSError:
                used_ports.append(port)
    return used_ports

def find_process_using_port(port: int) -> str:
    """Найти процесс, использующий указанный порт"""
    try:
        if os.name == 'nt':  # Windows
            result = subprocess.run(['netstat', '-ano'], capture_output=True, text=True)
            lines = result.stdout.split('\n')
            for line in lines:
                if f':{port}' in line:
                    parts = line.split()
                    pid = parts[-1]
                    return pid
        else:  # Linux/MacOS
            result = subprocess.run(['lsof', '-i', f':{port}'], capture_output=True, text=True)
            lines = result.stdout.split('\n')
            if len(lines) > 1:
                parts = lines[1].split()
                return parts[1]  # PID
    except Exception as e:
        print(f"Ошибка при поиске процесса: {e}")
    return ""

def kill_process(pid: str) -> bool:
    """Убить процесс по PID"""
    try:
        if os.name == 'nt':  # Windows
            subprocess.run(['taskkill', '/F', '/PID', pid], check=True)
        else:  # Linux/MacOS
            subprocess.run(['kill', '-9', pid], check=True)
        return True
    except Exception as e:
        print(f"Не удалось убить процесс {pid}: {e}")
        return False

def clear_ports(ports_to_clear: List[int]) -> None:
    """Очистить указанные порты"""
    for port in ports_to_clear:
        print(f"Проверка порта {port}...")
        pid = find_process_using_port(port)
        if pid:
            print(f"Порт {port} используется процессом с PID {pid}. Пытаюсь завершить...")
            if kill_process(pid):
                print(f"Процесс {pid} успешно завершен, порт {port} освобожден.")
            else:
                print(f"Не удалось завершить процесс {pid}, использующий порт {port}.")
        else:
            print(f"Порт {port} не используется или не удалось определить процесс.")

if __name__ == "__main__":
    import os
    
    # Порты из вашего docker-compose.yml
    ports_from_compose = [
        5432,  # postgres
        9000,  # minio
        9001,  # minio
        6379,  # redis
        5672,  # rabbitmq
        15672, # rabbitmq management
        9090,  # prometheus
        8010,  # consumer
        8000   # bot
    ]
    
    print("Скрипт очистки портов из docker-compose.yml")
    print("=" * 50)
    
    used_ports = get_used_ports()
    ports_to_clear = [port for port in ports_from_compose if port in used_ports]
    
    if not ports_to_clear:
        print("Все порты свободны. Ничего очищать не нужно.")
    else:
        print(f"Найдены занятые порты: {ports_to_clear}")
        clear_ports(ports_to_clear)
    
    print("\nДля полной очистки также выполните:")
    print("1. docker-compose down")
    print("2. docker system prune -f")
    print("3. Проверьте, что все контейнеры остановлены: docker ps -a")