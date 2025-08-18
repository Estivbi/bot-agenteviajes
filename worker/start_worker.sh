#!/bin/bash
# ============================================================================
# SCRIPT DE INICIO DEL WORKER DE ALERTAS DE VUELOS
# ============================================================================
# Este script inicia el worker en background y maneja logging

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Iniciando Worker de Alertas de Vuelos...${NC}"

# Cambiar al directorio del worker
cd "$(dirname "$0")"

# Verificar que existe el archivo de configuración
if [[ ! -f .env ]]; then
    echo -e "${YELLOW}⚠️  Archivo .env no encontrado${NC}"
    if [[ -f .env.example ]]; then
        echo -e "${BLUE}📋 Copiando .env.example a .env...${NC}"
        cp .env.example .env
        echo -e "${YELLOW}✏️  Por favor edita .env con tus configuraciones reales:${NC}"
        echo -e "   - RAPIDAPI_KEY"
        echo -e "   - TELEGRAM_BOT_TOKEN"
        echo -e "   - DB_* configuraciones"
        echo -e "${RED}❌ Configura .env y vuelve a ejecutar este script${NC}"
        exit 1
    else
        echo -e "${RED}❌ No se encontró .env.example - créalo manualmente${NC}"
        exit 1
    fi
fi

# Verificar Python 3
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 no está instalado${NC}"
    exit 1
fi

# Verificar dependencias
echo -e "${BLUE}📦 Verificando dependencias...${NC}"
python3 -c "import requests, psycopg2" 2>/dev/null
if [[ $? -ne 0 ]]; then
    echo -e "${YELLOW}⚠️  Instalando dependencias faltantes...${NC}"
    pip3 install requests psycopg2-binary python-dotenv
fi

# Verificar que el archivo flights_api.py existe
if [[ ! -f ../backend/flights_api.py ]]; then
    echo -e "${RED}❌ No se encontró ../backend/flights_api.py${NC}"
    exit 1
fi

# Crear directorio de logs
mkdir -p logs

# Función para manejar Ctrl+C
cleanup() {
    echo -e "\n${YELLOW}⏹️  Deteniendo worker...${NC}"
    if [[ ! -z "$worker_pid" ]]; then
        kill $worker_pid 2>/dev/null
    fi
    echo -e "${GREEN}✅ Worker detenido${NC}"
    exit 0
}

# Capturar señal de interrupción
trap cleanup SIGINT SIGTERM

# Mostrar configuración
echo -e "${BLUE}⚙️  Configuración:${NC}"
source .env
echo -e "   🗄️  Base de datos: $DB_HOST:$DB_PORT/$DB_NAME"
echo -e "   ⏰ Intervalo: ${WORKER_INTERVAL_MINUTES:-15} minutos"
echo -e "   📁 Log: logs/worker.log"

# Iniciar worker
echo -e "${GREEN}🚀 Iniciando worker de alertas...${NC}"
echo -e "${BLUE}💡 Presiona Ctrl+C para detener${NC}"
echo ""

# Ejecutar worker con logging
python3 worker.py 2>&1 | tee logs/worker.log &
worker_pid=$!

# Esperar a que termine
wait $worker_pid
