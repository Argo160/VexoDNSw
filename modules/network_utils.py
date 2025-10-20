# network_utils.py
import requests
import threading
import socket
from config import TRANSLATIONS, app_settings, save_settings

def get_public_ip():
    """Tries to get the public IP from reliable sources with a fallback."""
    try:
        return requests.get('https://icanhazip.com', timeout=5).text.strip()
    except requests.RequestException:
        try:
            return requests.get('https://v4.ident.me', timeout=5).text.strip()
        except requests.RequestException:
            return None

def update_ip_check_hosts():
    """
    Resolves and updates the IP addresses for IP checking services in the settings file.
    This runs in a background thread to not block the UI.
    """
    hosts_to_check = {
        'icanhazip.com': 'icanhazip_ip',
        'v4.ident.me': 'identme_ip'
    }
    
    something_changed = False
    for host, key in hosts_to_check.items():
        try:
            # Resolve the hostname to an IP address
            current_ip = socket.gethostbyname(host)
            stored_ip = app_settings.get(key)
            
            # If the IP has changed or is not stored yet, update it
            if current_ip != stored_ip:
                app_settings[key] = current_ip
                something_changed = True
        except socket.gaierror:
            # If DNS resolution fails, just skip and do nothing
            continue
            
    # Save settings only if there was a change
    if something_changed:
        save_settings()

def process_all_data(url, lang_code):
    """Process subscription data and IP updates"""
    final_result = {"success": False, "sub_data": None, "ip_status": None, "error": None}
    results = {}

    def get_public_ip_thread():
        results['public_ip'] = get_public_ip()

    def fetch_sub_data_thread():
        retries = 3
        last_exception = None

        for attempt in range(retries):
            try:
                if '/api/sub/' in url:
                    api_url = url
                elif '/sub/' in url:
                    api_url = url.replace('/sub/', '/api/sub/')
                else:
                    raise ValueError(TRANSLATIONS[lang_code]["error_url"])

                headers = {'User-Agent': 'VexoChecker/5.7'}
                response = requests.get(api_url, headers=headers, timeout=5)
                response.raise_for_status()
                sub_data = response.json()
                
                if sub_data.get('error'):
                    raise Exception(sub_data['error'])
                
                results['sub_data'] = sub_data
                results['api_url'] = api_url 
                results['error'] = None
                return

            except requests.exceptions.RequestException as e:
                last_exception = e
                if attempt < retries - 1:
                    time.sleep(1)
                    continue
                else:
                    break
            except (ValueError, Exception) as e:
                last_exception = e
                break

        if isinstance(last_exception, requests.exceptions.RequestException):
            results['error'] = TRANSLATIONS[lang_code]["error_connect"]
        elif isinstance(last_exception, ValueError):
            results['error'] = str(last_exception)
        else:
            results['error'] = TRANSLATIONS[lang_code]["error_unknown"]
        
        results['sub_data'] = None

    ip_thread = threading.Thread(target=get_public_ip_thread)
    sub_thread = threading.Thread(target=fetch_sub_data_thread)
    ip_thread.start()
    sub_thread.start()
    ip_thread.join()
    sub_thread.join()

    if results.get('error'):
        final_result["error"] = results['error']
        return final_result

    if not results.get('sub_data'):
        final_result["error"] = TRANSLATIONS[lang_code]["error_connect"]
        return final_result

    sub_data = results['sub_data']
    public_ip = results['public_ip']
    api_url = results['api_url']

    final_result["success"] = True
    final_result["sub_data"] = sub_data
    old_ip = sub_data.get('last_ip')
    
    if public_ip:
        if public_ip == old_ip:
            final_result["ip_status"] = {"key": "ip_no_change", "params": {"ip": public_ip}, "style": "success"}
        else:
            token = url.split('/sub/')[-1]
            update_ip_url = api_url.split('/api/sub/')[0] + '/api/update_ip'
            update_response = requests.post(update_ip_url, json={'token': token, 'ip': public_ip}, timeout=5)
            
            if update_response.ok:
                final_result["ip_status"] = {"key": "ip_changed_from_to", "params": {"old_ip": old_ip or "N/A", "new_ip": public_ip}, "style": "success"}
                final_result["sub_data"]["last_ip"] = public_ip
            else:
                update_data = update_response.json()
                if update_response.status_code == 409 and update_data.get('error_code') == 'IP_CONFLICT':
                    final_result["ip_status"] = {"key": "ip_conflict_error", "params": {}, "style": "danger"}
                else:
                    final_result["ip_status"] = {"key": "ip_update_fail", "params": {}, "style": "warning"}
    else:
        final_result["ip_status"] = {"key": "ip_not_found", "params": {}, "style": "warning"}
        
    return final_result
