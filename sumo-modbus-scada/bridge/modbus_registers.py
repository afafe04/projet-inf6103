"""
Documentation des registres Modbus
Configuration pour SCADA
"""

# ============================================
# INPUT REGISTERS (Fonction 04) - LECTURE SEULE
# Données de monitoring depuis SUMO
# ============================================

INPUT_REGISTERS = {
    # Données générales du trafic
    0: {
        'name': 'Vehicle Count',
        'unit': 'vehicles',
        'description': 'Nombre total de véhicules dans la simulation',
        'range': '0-1000'
    },
    1: {
        'name': 'Average Speed',
        'unit': 'km/h',
        'description': 'Vitesse moyenne de tous les véhicules',
        'range': '0-150'
    },
    2: {
        'name': 'Simulation Time',
        'unit': 'seconds',
        'description': 'Temps écoulé dans la simulation',
        'range': '0-86400'
    },
    3: {
        'name': 'Total Waiting Time',
        'unit': 'seconds',
        'description': 'Temps d\'attente cumulé de tous les véhicules',
        'range': '0-10000'
    },
    4: {
        'name': 'Jam Length',
        'unit': 'vehicles',
        'description': 'Nombre de véhicules en embouteillage',
        'range': '0-500'
    },
    5: {
        'name': 'Arrived Vehicles',
        'unit': 'vehicles',
        'description': 'Nombre de véhicules arrivés à destination',
        'range': '0-10000'
    },
    
    # Feu de circulation 1
    10: {
        'name': 'Traffic Light 1 Phase',
        'unit': 'phase',
        'description': 'Phase actuelle du feu 1',
        'range': '0-8'
    },
    11: {
        'name': 'Traffic Light 1 State',
        'unit': 'bitmap',
        'description': 'État du feu 1 (1=vert, 2=rouge, 4=jaune)',
        'range': '0-7'
    },
    
    # Feu de circulation 2
    20: {
        'name': 'Traffic Light 2 Phase',
        'unit': 'phase',
        'description': 'Phase actuelle du feu 2',
        'range': '0-8'
    },
    21: {
        'name': 'Traffic Light 2 State',
        'unit': 'bitmap',
        'description': 'État du feu 2 (1=vert, 2=rouge, 4=jaune)',
        'range': '0-7'
    },
    
    # Alarmes et événements
    30: {
        'name': 'Emergency Vehicles Count',
        'unit': 'vehicles',
        'description': 'Nombre de véhicules d\'urgence actifs',
        'range': '0-10'
    },
    31: {
        'name': 'Collision Count',
        'unit': 'events',
        'description': 'Nombre de collisions détectées',
        'range': '0-100'
    },
}

# ============================================
# HOLDING REGISTERS (Fonction 03/06/16) - LECTURE/ÉCRITURE
# Commandes de contrôle vers SUMO
# ============================================

HOLDING_REGISTERS = {
    # Contrôles système
    0: {
        'name': 'Emergency Mode',
        'unit': 'boolean',
        'description': 'Activer mode urgence (0=OFF, 1=ON)',
        'values': {0: 'Normal', 1: 'Emergency'},
        'writable': True
    },
    
    # Contrôle des feux
    1: {
        'name': 'Traffic Light 1 Manual Phase',
        'unit': 'phase',
        'description': 'Changer manuellement la phase du feu 1 (0=auto)',
        'range': '0-8',
        'writable': True
    },
    2: {
        'name': 'Traffic Light 2 Manual Phase',
        'unit': 'phase',
        'description': 'Changer manuellement la phase du feu 2 (0=auto)',
        'range': '0-8',
        'writable': True
    },
    
    # Paramètres de trafic
    3: {
        'name': 'Speed Limit Override',
        'unit': 'km/h',
        'description': 'Forcer une limite de vitesse (0=normal)',
        'range': '0-130',
        'writable': True
    },
    4: {
        'name': 'Reroute Command',
        'unit': 'command',
        'description': 'Recalculer les itinéraires (écrire 1 pour activer)',
        'values': {0: 'Idle', 1: 'Execute'},
        'writable': True
    },
    5: {
        'name': 'Phase Duration',
        'unit': 'seconds',
        'description': 'Durée des phases de feux (0=défaut)',
        'range': '10-120',
        'writable': True
    },
    
    # Durées des feux verts
    10: {
        'name': 'TL1 Green Duration',
        'unit': 'seconds',
        'description': 'Durée du vert pour feu 1',
        'range': '5-90',
        'writable': True
    },
    11: {
        'name': 'TL2 Green Duration',
        'unit': 'seconds',
        'description': 'Durée du vert pour feu 2',
        'range': '5-90',
        'writable': True
    },
    
    # Commandes système
    20: {
        'name': 'System Reset',
        'unit': 'command',
        'description': 'Réinitialiser les compteurs (écrire 1)',
        'values': {0: 'Idle', 1: 'Reset'},
        'writable': True
    },
    21: {
        'name': 'Pause Simulation',
        'unit': 'boolean',
        'description': 'Mettre en pause la simulation',
        'values': {0: 'Running', 1: 'Paused'},
        'writable': True
    },
}

# ============================================
# CONFIGURATION SCADA
# ============================================

SCADA_CONNECTION = {
    'protocol': 'Modbus TCP',
    'ip_address': 'modbus-bridge',  # ou IP du conteneur
    'port': 5020,
    'unit_id': 1,
    'timeout': 5000,  # ms
    'polling_rate': 1000,  # ms
}

# ============================================
# EXEMPLES D'UTILISATION
# ============================================

EXAMPLES = """
# 1. Lire le nombre de véhicules (avec pymodbus)
from pymodbus.client import ModbusTcpClient

client = ModbusTcpClient('localhost', port=5020)
client.connect()

# Lire input register 0 (Vehicle Count)
result = client.read_input_registers(0, 1, unit=1)
vehicle_count = result.registers[0]
print(f"Véhicules: {vehicle_count}")

# 2. Activer le mode urgence
# Écrire 1 dans holding register 0
client.write_register(0, 1, unit=1)

# 3. Changer la phase du feu 1
# Écrire la phase désirée (1-8) dans holding register 1
client.write_register(1, 3, unit=1)  # Phase 3

# 4. Lire la vitesse moyenne
result = client.read_input_registers(1, 1, unit=1)
avg_speed = result.registers[0]
print(f"Vitesse moyenne: {avg_speed} km/h")

client.close()
"""

if __name__ == "__main__":
    print("=" * 60)
    print("DOCUMENTATION REGISTRES MODBUS - SUMO SCADA")
    print("=" * 60)
    print("\n📊 INPUT REGISTERS (Lecture seule):")
    for addr, info in sorted(INPUT_REGISTERS.items()):
        print(f"  [{addr:3d}] {info['name']:30s} ({info['unit']})")
    
    print("\n⚙️  HOLDING REGISTERS (Lecture/Écriture):")
    for addr, info in sorted(HOLDING_REGISTERS.items()):
        print(f"  [{addr:3d}] {info['name']:30s} ({info['unit']})")
    
    print("\n🔌 Configuration connexion:")
    for key, value in SCADA_CONNECTION.items():
        print(f"  {key:20s}: {value}")
    
    print("\n" + EXAMPLES)
