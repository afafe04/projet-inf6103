#!/usr/bin/env python3
"""
SUMO to SCADA Bridge using Modbus TCP
Serveur Modbus TCP pour connecter SUMO avec des systèmes SCADA
"""

import sys
import time
import logging
import threading
import os
from pymodbus.server import StartTcpServer
from pymodbus.device import ModbusDeviceIdentification
from pymodbus.datastore import ModbusSequentialDataBlock, ModbusSlaveContext, ModbusServerContext
from pymodbus.transaction import ModbusRtuFramer, ModbusSocketFramer
import traci

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration Modbus
MODBUS_PORT = int(os.getenv('MODBUS_PORT', 5020))
SUMO_HOST = os.getenv('SUMO_HOST', 'sumo')
SUMO_PORT = int(os.getenv('SUMO_PORT', 8813))

# Mapping des registres Modbus
# Format: [Adresse] = Description
REGISTER_MAP = {
    # INPUT REGISTERS (lecture seule - données de SUMO)
    'INPUT': {
        0: 'Vehicle Count',
        1: 'Average Speed (km/h)',
        2: 'Simulation Time (seconds)',
        3: 'Total Waiting Time',
        4: 'Jam Length',
        5: 'Arrived Vehicles',
        10: 'Traffic Light 1 Phase',
        11: 'Traffic Light 1 State',
        20: 'Traffic Light 2 Phase',
        21: 'Traffic Light 2 State',
        30: 'Emergency Vehicles Count',
        31: 'Collision Count',
    },
    # HOLDING REGISTERS (lecture/écriture - commandes vers SUMO)
    'HOLDING': {
        0: 'Emergency Mode (0=OFF, 1=ON)',
        1: 'Traffic Light 1 Manual Phase',
        2: 'Traffic Light 2 Manual Phase',
        3: 'Speed Limit Override (km/h)',
        4: 'Reroute Command',
        5: 'Phase Duration (seconds)',
        10: 'TL1 Green Duration',
        11: 'TL2 Green Duration',
        20: 'System Reset',
        21: 'Pause Simulation',
    }
}

class ModbusDatastore:
    """Gestion du datastore Modbus"""
    
    def __init__(self):
        # Création des blocs de données
        # Discrete Inputs (1-bit, read-only)
        self.di = ModbusSequentialDataBlock(0, [0] * 100)
        
        # Coils (1-bit, read-write)
        self.co = ModbusSequentialDataBlock(0, [0] * 100)
        
        # Input Registers (16-bit, read-only)
        self.ir = ModbusSequentialDataBlock(0, [0] * 100)
        
        # Holding Registers (16-bit, read-write)
        self.hr = ModbusSequentialDataBlock(0, [0] * 100)
        
        # Contexte Modbus
        self.store = ModbusSlaveContext(
            di=self.di,
            co=self.co,
            ir=self.ir,
            hr=self.hr
        )
        self.context = ModbusServerContext(
                slaves={
                    0: self.store, 
                    1: self.store
                },
                single=False
        )
        
    def get_input_register(self, address):
        """Lire un input register"""
        return self.context[0].getValues(4, address, count=1)[0]
    
    def set_input_register(self, address, value):
        """Écrire un input register"""
        self.context[0].setValues(4, address, [int(value)])
    
    def get_holding_register(self, address):
        """Lire un holding register"""
        return self.context[0].getValues(3, address, count=1)[0]
    
    def set_holding_register(self, address, value):
        """Écrire un holding register"""
        self.context[0].setValues(3, address, [int(value)])

class SumoModbusBridge:
    """Bridge principal entre SUMO et Modbus"""
    
    def __init__(self):
        self.datastore = ModbusDatastore()
        self.running = False
        self.sumo_connected = False
        self.traffic_lights = []
        self.last_commands = {}
        
    def connect_to_sumo(self, max_retries=10):
        """Connexion à SUMO via TraCI"""
        logger.info(f"Connexion à SUMO sur {SUMO_HOST}:{SUMO_PORT}...")
        
        for attempt in range(max_retries):
            try:
                traci.init(port=SUMO_PORT, host=SUMO_HOST)
                self.sumo_connected = True
                logger.info("✓ Connecté à SUMO avec succès!")
                
                # Récupération des feux de circulation
                self.traffic_lights = traci.trafficlight.getIDList()
                logger.info(f"Feux de circulation détectés: {self.traffic_lights}")
                
                return True
                
            except Exception as e:
                logger.warning(f"Tentative {attempt + 1}/{max_retries} échouée: {e}")
                time.sleep(5)
        
        logger.error("Impossible de se connecter à SUMO")
        return False
    
    def update_sumo_data(self):
        """Lire les données de SUMO et mettre à jour les registres Modbus"""
        if not self.sumo_connected:
            return
        
        try:
            # Données des véhicules
            vehicle_ids = traci.vehicle.getIDList()
            vehicle_count = len(vehicle_ids)
            
            # Calcul de la vitesse moyenne
            if vehicle_count > 0:
                speeds = [traci.vehicle.getSpeed(vid) * 3.6 for vid in vehicle_ids]  # m/s -> km/h
                avg_speed = sum(speeds) / len(speeds)
                
                # Temps d'attente total
                waiting_times = [traci.vehicle.getWaitingTime(vid) for vid in vehicle_ids]
                total_waiting = sum(waiting_times)
            else:
                avg_speed = 0.0
                total_waiting = 0.0
            
            # Temps de simulation
            sim_time = traci.simulation.getTime()
            
            # Véhicules arrivés
            arrived = traci.simulation.getArrivedNumber()
            
            # Longueur des embouteillages
            try:
                edges = traci.edge.getIDList()
                jam_length = sum(traci.edge.getLastStepHaltingNumber(edge) for edge in edges[:10])
            except:
                jam_length = 0
            
            # Mise à jour des registres INPUT
            self.datastore.set_input_register(0, vehicle_count)
            self.datastore.set_input_register(1, int(avg_speed))
            self.datastore.set_input_register(2, int(sim_time))
            self.datastore.set_input_register(3, int(total_waiting))
            self.datastore.set_input_register(4, jam_length)
            self.datastore.set_input_register(5, arrived)
            
            # Mise à jour des états des feux de circulation
            for idx, tl_id in enumerate(self.traffic_lights[:4]):  # Max 4 feux
                try:
                    phase = traci.trafficlight.getPhase(tl_id)
                    state = traci.trafficlight.getRedYellowGreenState(tl_id)
                    
                    # Conversion de l'état en valeur numérique
                    state_value = self._state_to_int(state)
                    
                    base_addr = 10 + (idx * 10)
                    self.datastore.set_input_register(base_addr, phase)
                    self.datastore.set_input_register(base_addr + 1, state_value)
                except Exception as e:
                    logger.debug(f"Erreur lecture feu {tl_id}: {e}")
            
            # Compter les véhicules d'urgence
            emergency_count = sum(1 for vid in vehicle_ids 
                                 if traci.vehicle.getTypeID(vid) == "emergency")
            self.datastore.set_input_register(30, emergency_count)
            
        except Exception as e:
            logger.error(f"Erreur mise à jour données SUMO: {e}")
    
    def process_modbus_commands(self):
        """Lire les commandes Modbus et les appliquer à SUMO"""
        if not self.sumo_connected:
            return
        
        try:
            # Mode urgence
            emergency_mode = self.datastore.get_holding_register(0)
            if emergency_mode == 1 and self.last_commands.get('emergency') != 1:
                logger.info("🚨 MODE URGENCE ACTIVÉ")
                self._activate_emergency_mode()
                self.last_commands['emergency'] = 1
            elif emergency_mode == 0 and self.last_commands.get('emergency') == 1:
                logger.info("✓ Mode urgence désactivé")
                self.last_commands['emergency'] = 0
            
            # Contrôle manuel des feux
            for idx, tl_id in enumerate(self.traffic_lights[:2]):
                reg_addr = 1 + idx
                manual_phase = self.datastore.get_holding_register(reg_addr)
                
                if manual_phase > 0 and self.last_commands.get(f'tl{idx}') != manual_phase:
                    logger.info(f"Changement manuel feu {tl_id} -> Phase {manual_phase}")
                    try:
                        traci.trafficlight.setPhase(tl_id, manual_phase - 1)
                        self.last_commands[f'tl{idx}'] = manual_phase
                    except Exception as e:
                        logger.error(f"Erreur changement phase: {e}")
            
            # Limitation de vitesse
            speed_limit = self.datastore.get_holding_register(3)
            if speed_limit > 0 and self.last_commands.get('speed') != speed_limit:
                logger.info(f"Nouvelle limite de vitesse: {speed_limit} km/h")
                for vid in traci.vehicle.getIDList():
                    try:
                        traci.vehicle.setMaxSpeed(vid, speed_limit / 3.6)  # km/h -> m/s
                    except:
                        pass
                self.last_commands['speed'] = speed_limit
            
            # Reset système
            reset_cmd = self.datastore.get_holding_register(20)
            if reset_cmd == 1:
                logger.info("🔄 Reset système demandé")
                self.datastore.set_holding_register(20, 0)  # Clear command
                # Réinitialiser les compteurs
                for addr in range(100):
                    self.datastore.set_input_register(addr, 0)
            
        except Exception as e:
            logger.error(f"Erreur traitement commandes: {e}")
    
    def _state_to_int(self, state_str):
        """Convertir l'état des feux en entier"""
        # G=vert, r=rouge, y=jaune
        value = 0
        if 'G' in state_str:
            value += 1  # Vert
        if 'r' in state_str:
            value += 2  # Rouge
        if 'y' in state_str:
            value += 4  # Jaune
        return value
    
    def _activate_emergency_mode(self):
        """Activer le mode urgence - tous les feux au vert"""
        for tl_id in self.traffic_lights:
            try:
                # Mettre tous les feux au vert
                state = traci.trafficlight.getRedYellowGreenState(tl_id)
                green_state = 'G' * len(state)
                traci.trafficlight.setRedYellowGreenState(tl_id, green_state)
            except Exception as e:
                logger.error(f"Erreur mode urgence pour {tl_id}: {e}")
    
    def sumo_loop(self):
        """Boucle principale SUMO"""
        logger.info("Démarrage de la boucle SUMO...")
        step_count = 0
        
        while self.running:
            try:
                if self.sumo_connected:
                    # Avancer la simulation
                    traci.simulationStep()
                    step_count += 1
                    
                    # Mise à jour des données
                    self.update_sumo_data()
                    
                    # Traitement des commandes
                    self.process_modbus_commands()
                    
                    # Log toutes les 100 étapes
                    if step_count % 100 == 0:
                        vehicle_count = self.datastore.get_input_register(0)
                        avg_speed = self.datastore.get_input_register(1)
                        logger.info(f"Step {step_count}: Véhicules={vehicle_count}, "
                                  f"Vitesse moy={avg_speed} km/h")
                    
                    # Petite pause
                    time.sleep(0.05)
                else:
                    time.sleep(1)
                    
            except Exception as e:
                logger.error(f"Erreur dans boucle SUMO: {e}")
                time.sleep(1)
    
    def start_modbus_server(self):
        """Démarrer le serveur Modbus TCP"""
        logger.info(f"Démarrage serveur Modbus TCP sur port {MODBUS_PORT}...")
        
        # Identity du serveur
        identity = ModbusDeviceIdentification()
        identity.VendorName = 'SUMO Traffic Control'
        identity.ProductCode = 'STC'
        identity.VendorUrl = 'http://sumo.dlr.de'
        identity.ProductName = 'SUMO Modbus Bridge'
        identity.ModelName = 'v1.0'
        identity.MajorMinorRevision = '1.0.0'
        
        # FIXED: Démarrage du serveur dans un thread avec kwargs au lieu de args
        server_thread = threading.Thread(
            target=StartTcpServer,
            kwargs={
                'context': self.datastore.context,
                'identity': identity,
                'address': ('0.0.0.0', MODBUS_PORT),
                'framer': ModbusSocketFramer
            },
            daemon=True
        )
        server_thread.start()
        logger.info(f"✓ Serveur Modbus démarré sur 0.0.0.0:{MODBUS_PORT}")
    
    def run(self):
        """Fonction principale"""
        try:
            # Démarrer le serveur Modbus
            self.start_modbus_server()
            time.sleep(2)
            
            # Connecter à SUMO
            if not self.connect_to_sumo():
                logger.error("Échec de connexion à SUMO")
                return
            
            # Démarrer la boucle SUMO
            self.running = True
            logger.info("🚀 Bridge Modbus-SUMO opérationnel!")
            logger.info(f"📊 Registres INPUT (lecture): {list(REGISTER_MAP['INPUT'].values())[:6]}")
            logger.info(f"⚙️  Registres HOLDING (contrôle): {list(REGISTER_MAP['HOLDING'].values())[:6]}")
            
            self.sumo_loop()
            
        except KeyboardInterrupt:
            logger.info("Arrêt demandé...")
        except Exception as e:
            logger.error(f"Erreur fatale: {e}", exc_info=True)
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Nettoyage"""
        logger.info("Nettoyage des ressources...")
        self.running = False
        
        if self.sumo_connected:
            try:
                traci.close()
                logger.info("✓ SUMO fermé")
            except:
                pass

if __name__ == "__main__":
    bridge = SumoModbusBridge()
    bridge.run()
