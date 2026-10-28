import subprocess
import platform
import json
import requests

def get_network_report():
    # Check internet connection
    try:
        requests.get("http://www.google.com", timeout=5)
        internet_connected = True
    except requests.ConnectionError:
        return "❌ Internet is NOT Connected!"

    # Get Wi-Fi details (SSID, Channel, Speed, Signal Strength)
    wifi_details = {"SSID": "Unknown", "Channel": "Unknown", "Speed": "Unknown", "Signal Strength": "Unknown", "Password": "Unknown"}

    if platform.system() == "Windows":
        try:
            result = subprocess.run(["netsh", "wlan", "show", "interfaces"], capture_output=True, text=True)
            output = result.stdout

            for line in output.split("\n"):
                if "SSID" in line and "BSSID" not in line:
                    wifi_details["SSID"] = line.split(":")[1].strip()
                elif "Channel" in line:
                    wifi_details["Channel"] = line.split(":")[1].strip()
                elif "Receive rate" in line:
                    wifi_details["Speed"] = line.split(":")[1].strip()
                elif "Signal" in line:
                    wifi_details["Signal Strength"] = line.split(":")[1].strip()

            # Get saved Wi-Fi password
            password_result = subprocess.run(["netsh", "wlan", "show", "profile", wifi_details["SSID"], "key=clear"], capture_output=True, text=True)
            for line in password_result.stdout.split("\n"):
                if "Key Content" in line:
                    wifi_details["Password"] = line.split(":")[1].strip()
                    break

        except Exception:
            pass

    # Get location details using IP
    try:
        response = requests.get("http://ip-api.com/json")
        location = response.json()
    except Exception:
        location = {}

    # Format Output
    formatted = f"""
    🌐 Network Report

    ✅ Internet Status: Connected  

    📡Wi-Fi Details
    - SSID: {wifi_details.get("SSID", "Unknown")}
    - Channel: {wifi_details.get("Channel", "Unknown")}
    - Speed: {wifi_details.get("Speed", "Unknown")}
    - Signal Strength: {wifi_details.get("Signal Strength", "Unknown")}
    - Password: {wifi_details.get("Password", "Unknown")}

    🌍Location Information
    - City: {location.get("city", "Unknown")}
    - Region: {location.get("regionName", "Unknown")}
    - Country: {location.get("country", "Unknown")}
    - ISP: {location.get("isp", "Unknown")}
    - Latitude: {location.get("lat", "Unknown")}
    - Longitude: {location.get("lon", "Unknown")}
    """
    
    return formatted.strip()

# Call the function and print the report
print(get_network_report())
