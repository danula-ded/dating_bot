#!/bin/bash

# Список портов для проверки
ports=(9000 9001 5432 6379 8000 5672 15672 9090)

echo "Подчистка портов: ${ports[@]}"

for port in "${ports[@]}"; do
  echo "Проверка порта $port..."
  # Найти процесс, использующий порт
  pid=$(sudo lsof -t -i :$port)
  if [ -n "$pid" ]; then
    echo " + Найден процесс PID $pid, использующий порт $port. Завершаем..."
    sudo kill -9 $pid
    echo "   Процесс PID $pid завершен."
  else
    echo "Порт $port свободен."
  fi
done

echo "Подчистка завершена!"
