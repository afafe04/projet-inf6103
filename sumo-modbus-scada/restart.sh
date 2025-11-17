#!/bin/bash

echo "🔄 Redémarrage propre du système"
echo "================================="

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 1. Arrêter tout
echo -e "\n${YELLOW}[1/5]${NC} Arrêt des conteneurs..."
docker-compose down -v
sleep 2

# 2. Nettoyer les conteneurs échoués
echo -e "\n${YELLOW}[2/5]${NC} Nettoyage..."
docker system prune -f

# 3. Vérifier les fichiers
echo -e "\n${YELLOW}[3/5]${NC} Vérification des fichiers..."
if [ ! -f "sumo-data/heavy_traffic.sumocfg" ]; then
    echo "❌ Fichier heavy_traffic.sumocfg manquant!"
    echo "Veuillez copier vos fichiers SUMO dans sumo-data/"
    exit 1
fi
echo -e "${GREEN}✓${NC} Fichiers SUMO OK"

# 4. Rebuild sans cache
echo -e "\n${YELLOW}[4/5]${NC} Reconstruction des images..."
docker-compose build --no-cache modbus-bridge

# 5. Démarrer progressivement
echo -e "\n${YELLOW}[5/5]${NC} Démarrage progressif..."

# Démarrer SUMO d'abord
echo "Démarrage SUMO..."
docker-compose up -d sumo
sleep 10

# Vérifier que SUMO fonctionne
if docker ps | grep -q sumo-simulation; then
    echo -e "${GREEN}✓${NC} SUMO démarré"
else
    echo "❌ SUMO n'a pas démarré"
    docker logs sumo-simulation
    exit 1
fi

# Démarrer le bridge
echo "Démarrage Bridge Modbus..."
docker-compose up -d modbus-bridge
sleep 5

# Démarrer le reste
echo "Démarrage des autres services..."
docker-compose up -d

sleep 5

# Statut final
echo ""
echo "================================="
echo "Statut des conteneurs:"
echo "================================="
docker-compose ps

echo ""
echo "================================="
echo "Logs du Bridge:"
echo "================================="
docker logs --tail 20 modbus-bridge

echo ""
echo "Pour voir les logs en temps réel:"
echo "  docker-compose logs -f modbus-bridge"
