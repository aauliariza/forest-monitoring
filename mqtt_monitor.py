#!/usr/bin/env python3
"""
MQTT Monitoring Script untuk Forest Monitoring System
Menampilkan komunikasi MQTT secara real-time
"""

import paho.mqtt.client as mqtt
import json
from datetime import datetime
from colorama import Fore, Back, Style, init

# Initialize colorama untuk colored output
init(autoreset=True)

# Statistics
stats = {
    "total_messages": 0,
    "by_sensor": {},
    "by_status": {"normal": 0, "warning": 0, "danger": 0}
}

def on_connect(client, userdata, flags, rc):
    """Callback ketika subscriber berhasil connect"""
    timestamp = datetime.now().strftime('%H:%M:%S')
    if rc == 0:
        print(f"{Fore.GREEN}[{timestamp}] ✓ TERHUBUNG ke MQTT Broker (localhost:1883)")
        print(f"{Fore.GREEN}[{timestamp}] ✓ Subscribe ke topic: 'sensors/telemetry'")
        client.subscribe("sensors/telemetry")
        print(f"{Fore.CYAN}{'='*70}")
        print(f"{Fore.CYAN}Menunggu pesan MQTT dari sensor... (Tekan Ctrl+C untuk berhenti)")
        print(f"{Fore.CYAN}{'='*70}\n")
    else:
        print(f"{Fore.RED}[{timestamp}] ✗ Koneksi gagal, kode error: {rc}")

def on_disconnect(client, userdata, rc):
    """Callback ketika disconnected"""
    timestamp = datetime.now().strftime('%H:%M:%S')
    if rc != 0:
        print(f"{Fore.YELLOW}[{timestamp}] ⚠ Koneksi terputus (kode: {rc})")

def on_message(client, userdata, msg):
    """Callback ketika menerima pesan MQTT"""
    global stats
    timestamp = datetime.now().strftime('%H:%M:%S')
    
    try:
        # Parse JSON payload
        payload = json.loads(msg.payload.decode())
        
        # Extract fields
        sensor_id = payload.get('sensor_id', 'unknown')
        sensor_type = payload.get('sensor_type', 'unknown')
        location = payload.get('location', 'unknown')
        data = payload.get('data', {})
        status = payload.get('status', 'unknown').upper()
        message_timestamp = payload.get('timestamp', 'unknown')
        
        # Update stats
        stats["total_messages"] += 1
        if sensor_id not in stats["by_sensor"]:
            stats["by_sensor"][sensor_id] = 0
        stats["by_sensor"][sensor_id] += 1
        if status.lower() in stats["by_status"]:
            stats["by_status"][status.lower()] += 1
        
        # Colorize status
        if status == "DANGER":
            status_colored = f"{Fore.RED}{Back.WHITE}{status}{Style.RESET_ALL}"
        elif status == "WARNING":
            status_colored = f"{Fore.YELLOW}{Style.BRIGHT}{status}{Style.RESET_ALL}"
        else:
            status_colored = f"{Fore.GREEN}{status}{Style.RESET_ALL}"
        
        # Display message
        print(f"{Fore.CYAN}[{timestamp}]{Style.RESET_ALL} 📡 MQTT MESSAGE")
        print(f"  {Fore.BLUE}Topic:{Style.RESET_ALL} {msg.topic}")
        print(f"  {Fore.BLUE}Sensor ID:{Style.RESET_ALL} {sensor_id} ({sensor_type})")
        print(f"  {Fore.BLUE}Lokasi:{Style.RESET_ALL} {location}")
        print(f"  {Fore.BLUE}Data:{Style.RESET_ALL} {data}")
        print(f"  {Fore.BLUE}Status:{Style.RESET_ALL} {status_colored}")
        print(f"  {Fore.BLUE}Timestamp Sensor:{Style.RESET_ALL} {message_timestamp}")
        
        # Show statistics every 10 messages
        if stats["total_messages"] % 10 == 0:
            print(f"\n{Fore.MAGENTA}📊 STATISTIK (Total: {stats['total_messages']} pesan){Style.RESET_ALL}")
            for sensor, count in stats["by_sensor"].items():
                print(f"  - {sensor}: {count} pesan")
            print(f"  Status: Normal={stats['by_status']['normal']}, "
                  f"Warning={stats['by_status']['warning']}, "
                  f"Danger={stats['by_status']['danger']}")
            print()
        else:
            print(f"  {Fore.LIGHTBLACK_EX}(Total pesan diterima: {stats['total_messages']}){Style.RESET_ALL}\n")
            
    except json.JSONDecodeError as e:
        print(f"{Fore.RED}[{timestamp}] ✗ JSON Parse Error: {str(e)}")
        print(f"{Fore.RED}  Raw message: {msg.payload.decode()}\n")
    except Exception as e:
        print(f"{Fore.RED}[{timestamp}] ✗ Error: {str(e)}\n")

def main():
    """Main function"""
    print(f"\n{Fore.CYAN}{'='*70}")
    print(f"{Fore.CYAN}🌳 FOREST MONITORING - MQTT SUBSCRIBER")
    print(f"{Fore.CYAN}{'='*70}\n")
    
    # Create client
    client = mqtt.Client("mqtt_monitor_client")
    
    # Set callbacks
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_message = on_message
    
    # Connect to broker
    print(f"{Fore.YELLOW}🔌 Menghubungkan ke MQTT Broker...")
    try:
        client.connect("localhost", 1883, keepalive=60)
    except ConnectionRefusedError:
        print(f"{Fore.RED}✗ Koneksi ditolak!")
        print(f"{Fore.RED}  Pastikan MQTT Broker running di localhost:1883")
        print(f"{Fore.RED}  Jalankan: docker-compose up -d mqtt-broker")
        return
    except Exception as e:
        print(f"{Fore.RED}✗ Error: {str(e)}")
        return
    
    # Loop forever
    try:
        client.loop_forever()
    except KeyboardInterrupt:
        print(f"\n\n{Fore.YELLOW}⚠ Menghentikan subscriber...")
        print(f"\n{Fore.MAGENTA}{'='*70}")
        print(f"{Fore.MAGENTA}📊 STATISTIK FINAL")
        print(f"{Fore.MAGENTA}{'='*70}")
        print(f"  Total pesan diterima: {stats['total_messages']}")
        print(f"  Per sensor:")
        for sensor, count in stats["by_sensor"].items():
            print(f"    - {sensor}: {count} pesan")
        print(f"  Per status:")
        print(f"    - NORMAL: {stats['by_status']['normal']}")
        print(f"    - WARNING: {stats['by_status']['warning']}")
        print(f"    - DANGER: {stats['by_status']['danger']}")
        print(f"{Fore.MAGENTA}{'='*70}\n")
        client.disconnect()

if __name__ == "__main__":
    main()
