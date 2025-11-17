#!/usr/bin/env python3
"""
Script de test client Modbus
Pour tester la connexion au bridge SUMO-Modbus
"""

from pymodbus.client import ModbusTcpClient
import time
import sys

# Configuration
MODBUS_HOST = 'localhost'
MODBUS_PORT = 5020
UNIT_ID = 1

def test_connection():
    """Tester la connexion Modbus"""
    print("🔌 Test de connexion Modbus...")
    print(f"   Host: {MODBUS_HOST}")
    print(f"   Port: {MODBUS_PORT}")
    
    client = ModbusTcpClient(MODBUS_HOST, port=MODBUS_PORT)
    
    if client.connect():
        print("✓ Connexion réussie!\n")
        return client
    else:
        print("✗ Échec de connexion")
        sys.exit(1)

def read_monitoring_data(client):
    """Lire les données de monitoring"""
    print("=" * 60)
    print("📊 DONNÉES DE MONITORING (INPUT REGISTERS)")
    print("=" * 60)
    
    try:
        # Lire les registres de monitoring
        result = client.read_input_registers(0, 32, unit=UNIT_ID)
        
        if result.isError():
            print("✗ Erreur de lecture")
            return
        
        regs = result.registers
        
        print(f"Nombre de véhicules       : {regs[0]}")
        print(f"Vitesse moyenne           : {regs[1]} km/h")
        print(f"Temps simulation          : {regs[2]} s")
        print(f"Temps d'attente total     : {regs[3]} s")
        print(f"Longueur embouteillages   : {regs[4]} véhicules")
        print(f"Véhicules arrivés         : {regs[5]}")
        print(f"\nFeu 1 - Phase             : {regs[10]}")
        print(f"Feu 1 - État              : {regs[11]}")
        print(f"Feu 2 - Phase             : {regs[20]}")
        print(f"Feu 2 - État              : {regs[21]}")
        print(f"\nVéhicules d'urgence       : {regs[30]}")
        print(f"Collisions                : {regs[31]}")
        
    except Exception as e:
        print(f"✗ Erreur: {e}")

def read_control_registers(client):
    """Lire les registres de contrôle"""
    print("\n" + "=" * 60)
    print("⚙️  REGISTRES DE CONTRÔLE (HOLDING REGISTERS)")
    print("=" * 60)
    
    try:
        result = client.read_holding_registers(0, 22, unit=UNIT_ID)
        
        if result.isError():
            print("✗ Erreur de lecture")
            return
        
        regs = result.registers
        
        print(f"Mode urgence              : {'ACTIVÉ' if regs[0] == 1 else 'Désactivé'}")
        print(f"Feu 1 phase manuelle      : {regs[1]} (0=auto)")
        print(f"Feu 2 phase manuelle      : {regs[2]} (0=auto)")
        print(f"Limite vitesse forcée     : {regs[3]} km/h (0=normal)")
        print(f"Commande reroutage        : {regs[4]}")
        print(f"Durée phase               : {regs[5]} s")
        print(f"Durée vert feu 1          : {regs[10]} s")
        print(f"Durée vert feu 2          : {regs[11]} s")
        print(f"Reset système             : {regs[20]}")
        print(f"Pause simulation          : {'OUI' if regs[21] == 1 else 'NON'}")
        
    except Exception as e:
        print(f"✗ Erreur: {e}")

def test_write_commands(client):
    """Tester les commandes d'écriture"""
    print("\n" + "=" * 60)
    print("✍️  TEST DES COMMANDES")
    print("=" * 60)
    
    # Test 1: Activer mode urgence
    print("\n1️⃣  Activation du mode urgence...")
    result = client.write_register(0, 1, unit=UNIT_ID)
    if not result.isError():
        print("   ✓ Mode urgence activé")
        time.sleep(2)
        
        # Désactiver
        client.write_register(0, 0, unit=UNIT_ID)
        print("   ✓ Mode urgence désactivé")
    else:
        print("   ✗ Échec")
    
    # Test 2: Changer phase feu 1
    print("\n2️⃣  Changement de phase feu 1...")
    result = client.write_register(1, 2, unit=UNIT_ID)
    if not result.isError():
        print("   ✓ Feu 1 mis en phase 2")
        time.sleep(2)
        
        # Remettre en auto
        client.write_register(1, 0, unit=UNIT_ID)
        print("   ✓ Feu 1 remis en automatique")
    else:
        print("   ✗ Échec")
    
    # Test 3: Limiter vitesse
    print("\n3️⃣  Limitation de vitesse à 50 km/h...")
    result = client.write_register(3, 50, unit=UNIT_ID)
    if not result.isError():
        print("   ✓ Limite de vitesse appliquée")
        time.sleep(2)
        
        # Remettre normal
        client.write_register(3, 0, unit=UNIT_ID)
        print("   ✓ Limite normale restaurée")
    else:
        print("   ✗ Échec")

def monitor_continuous(client, duration=30):
    """Monitoring continu"""
    print("\n" + "=" * 60)
    print(f"📡 MONITORING CONTINU ({duration}s)")
    print("=" * 60)
    print("\nTemps | Véhicules | Vitesse moy | Attente | Embouteillage")
    print("-" * 60)
    
    start_time = time.time()
    
    try:
        while time.time() - start_time < duration:
            result = client.read_input_registers(0, 5, unit=UNIT_ID)
            
            if not result.isError():
                regs = result.registers
                elapsed = int(time.time() - start_time)
                print(f"{elapsed:4d}s | {regs[0]:9d} | {regs[1]:11d} | "
                      f"{regs[3]:7d} | {regs[4]:13d}")
            
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n⏹️  Arrêt du monitoring")

def interactive_mode(client):
    """Mode interactif"""
    print("\n" + "=" * 60)
    print("🎮 MODE INTERACTIF")
    print("=" * 60)
    print("\nCommandes disponibles:")
    print("  1 - Activer/désactiver mode urgence")
    print("  2 - Changer phase feu 1")
    print("  3 - Changer phase feu 2")
    print("  4 - Définir limite de vitesse")
    print("  r - Lire données monitoring")
    print("  c - Lire registres contrôle")
    print("  m - Monitoring continu")
    print("  q - Quitter")
    
    while True:
        try:
            cmd = input("\n>>> ").strip().lower()
            
            if cmd == 'q':
                break
            elif cmd == 'r':
                read_monitoring_data(client)
            elif cmd == 'c':
                read_control_registers(client)
            elif cmd == 'm':
                monitor_continuous(client, 20)
            elif cmd == '1':
                mode = input("Mode urgence (0=OFF, 1=ON): ")
                client.write_register(0, int(mode), unit=UNIT_ID)
                print("✓ Commande envoyée")
            elif cmd == '2':
                phase = input("Phase feu 1 (0-8, 0=auto): ")
                client.write_register(1, int(phase), unit=UNIT_ID)
                print("✓ Commande envoyée")
            elif cmd == '3':
                phase = input("Phase feu 2 (0-8, 0=auto): ")
                client.write_register(2, int(phase), unit=UNIT_ID)
                print("✓ Commande envoyée")
            elif cmd == '4':
                speed = input("Limite vitesse (0-130 km/h, 0=normal): ")
                client.write_register(3, int(speed), unit=UNIT_ID)
                print("✓ Commande envoyée")
            else:
                print("Commande inconnue")
                
        except KeyboardInterrupt:
            print("\n")
            break
        except Exception as e:
            print(f"Erreur: {e}")

def main():
    """Fonction principale"""
    print("=" * 60)
    print("🚦 CLIENT MODBUS - TEST SUMO SCADA")
    print("=" * 60)
    
    # Connexion
    client = test_connection()
    
    try:
        # Tests automatiques
        read_monitoring_data(client)
        read_control_registers(client)
        test_write_commands(client)
        
        # Mode interactif
        response = input("\n▶️  Lancer le mode interactif? (o/n): ")
        if response.lower() == 'o':
            interactive_mode(client)
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Arrêt demandé")
    finally:
        client.close()
        print("\n✓ Déconnexion Modbus")

if __name__ == "__main__":
    main()
