# dns_manager.py
import subprocess
import ctypes
import sys
import re

def is_admin():
    """Check if the application has admin privileges"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def get_main_executable_path():
    """Gets the absolute path of the main executable from the OS."""
    buffer = ctypes.create_unicode_buffer(260)
    ctypes.windll.kernel32.GetModuleFileNameW(None, buffer, 260)
    return buffer.value

def get_active_interface_names():
    """
    Finds active network interface names using a three-stage fallback system
    to ensure maximum compatibility across all Windows versions.
    """
    # Stage 1: Best and most reliable method (WMIC)
    try:
        command = 'wmic path Win32_NetworkAdapter where "NetConnectionStatus=2" get NetConnectionID'
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True, check=True,
            encoding='utf-8', creationflags=subprocess.CREATE_NO_WINDOW
        )
        lines = result.stdout.strip().split('\n')
        active_interfaces = [name.strip() for name in lines[1:] if name.strip()]
        if active_interfaces:
            return active_interfaces
    except Exception:
        pass

    # Stage 2: Modern method (PowerShell)
    try:
        command = "powershell -ExecutionPolicy Bypass -Command \"Get-NetAdapter -Physical | Where-Object { $_.Status -eq 'Up' } | ForEach-Object { $_.Name }\""
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True, check=True,
            encoding='utf-8', creationflags=subprocess.CREATE_NO_WINDOW
        )
        active_interfaces = [name.strip() for name in result.stdout.strip().split('\n') if name.strip()]
        if active_interfaces:
            return active_interfaces
    except Exception:
        pass

    # Stage 3: Legacy method (netsh)
    try:
        command = 'netsh interface ipv4 show interfaces'
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True, check=True,
            encoding='utf-8', creationflags=subprocess.CREATE_NO_WINDOW
        )
        lines = result.stdout.strip().split('\n')
        active_interfaces = []
        for line in lines[2:]:
            if 'connected' in line.lower():
                parts = line.strip().split()
                interface_name = " ".join(parts[3:])
                active_interfaces.append(interface_name)
        if active_interfaces:
            return active_interfaces
    except Exception:
        pass

    return []

def get_current_dns_servers(interface_name):
    """Gets the currently configured DNS servers for a specific interface."""
    try:
        command = f'netsh interface ipv4 show dnsservers name="{interface_name}"'
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True, check=True,
            encoding='utf-8', creationflags=subprocess.CREATE_NO_WINDOW
        )
        dns_servers = re.findall(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', result.stdout)
        return [dns for dns in dns_servers if dns != "0.0.0.0"]
    except (subprocess.CalledProcessError, FileNotFoundError):
        return []

def check_dns_status(target_dns):
    """Checks if the app's DNS is set on any active network interface."""
    if not target_dns:
        return False

    active_interfaces = get_active_interface_names()
    for interface in active_interfaces:
        current_dns_list = get_current_dns_servers(interface)
        if target_dns in current_dns_list:
            return True

    return False

def set_dns(dns_ip1, dns_ip2=None):
    """Set DNS on all active interfaces"""
    interfaces = get_active_interface_names()
    if not interfaces:
        return {"success": False, "error_key": "no_active_interface"}
    
    for name in interfaces:
        try:
            flags = subprocess.CREATE_NO_WINDOW
            subprocess.run(
                f'netsh interface ipv4 set dnsservers name="{name}" static {dns_ip1} primary',
                check=True, shell=True, capture_output=True, creationflags=flags
            )
            if dns_ip2:
                subprocess.run(
                    f'netsh interface ipv4 add dnsservers name="{name}" address={dns_ip2} index=2',
                    shell=True, capture_output=True, creationflags=flags
                )
            return {"success": True, "dns_ip": dns_ip1}
        except subprocess.CalledProcessError:
            continue
    
    return {"success": False, "error_key": "dns_set_fail_message"}

def unset_dns():
    """Unset DNS on all active interfaces"""
    interfaces = get_active_interface_names()
    if not interfaces:
        return {"success": False, "error_key": "no_active_interface"}
    
    success = any(
        subprocess.run(
            f'netsh interface ipv4 set dnsservers name="{name}" source=dhcp',
            shell=True, capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW
        ).returncode == 0
        for name in interfaces
    )
    
    return {"success": success, "error_key": "dns_unset_fail_message"}

def unset_dns_synchronously():
    """
    A simplified, synchronous function to unset DNS on all active interfaces.
    This is used for the exit process to ensure DNS is reset before closing.
    """
    interfaces = get_active_interface_names()
    if not interfaces:
        return False

    success = False
    for name in interfaces:
        try:
            result = subprocess.run(
                f'netsh interface ipv4 set dnsservers name="{name}" source=dhcp',
                shell=True, capture_output=True, check=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            if result.returncode == 0:
                success = True
        except subprocess.CalledProcessError:
            continue
    
    return success