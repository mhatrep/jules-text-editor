import subprocess
import platform
import json
import os
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from datetime import datetime

# Helper to format datetime objects, similar to certificate_analyzer
def _format_datetime_obj(dt_obj):
    if dt_obj is None:
        return "N/A"
    if dt_obj.tzinfo is None:
        import datetime as dt_module
        dt_obj = dt_obj.replace(tzinfo=dt_module.timezone.utc)
    return dt_obj.strftime("%Y-%m-%d %H:%M:%S %Z")

def _parse_pem_certificate_summary(pem_data_bytes, source_file_hint="PEM Data"):
    """
    Parses basic details from PEM certificate data.
    Returns a dictionary with summary details or None if parsing fails.
    """
    try:
        cert = x509.load_pem_x509_certificate(pem_data_bytes, default_backend())
        subject_attrs = {attr.oid._name: attr.value for rdn in cert.subject for attr in rdn}
        issuer_attrs = {attr.oid._name: attr.value for rdn in cert.issuer for attr in rdn}

        valid_from = cert.not_valid_before_utc if hasattr(cert, 'not_valid_before_utc') else cert.not_valid_before
        valid_to = cert.not_valid_after_utc if hasattr(cert, 'not_valid_after_utc') else cert.not_valid_after

        return {
            "subject_cn": subject_attrs.get("commonName", cert.subject.rfc4514_string()), # Fallback to full subject if CN missing
            "issuer_cn": issuer_attrs.get("commonName", cert.issuer.rfc4514_string()),   # Fallback to full issuer if CN missing
            "serial_number": cert.serial_number.to_bytes((cert.serial_number.bit_length() + 7) // 8, 'big').hex(':'),
            "thumbprint_sha256": cert.fingerprint(hashes.SHA256()).hex(':'), # Use colon for consistency
            "valid_from": _format_datetime_obj(valid_from),
            "valid_to": _format_datetime_obj(valid_to),
            "pem_data": pem_data_bytes.decode('utf-8', errors='ignore'),
            "source_detail": source_file_hint
        }
    except Exception:
        # import traceback; print(f"Error parsing PEM summary from {source_file_hint}: {traceback.format_exc()}")
        return None

def get_system_certificates_windows():
    results = []
    cert_stores_map = {
        "CurrentUser\\My": "User Personal", "LocalMachine\\My": "Machine Personal",
        "CurrentUser\\Root": "User Tr.Roots", "LocalMachine\\Root": "Mach. Tr.Roots", # Shorter names for UI
        "CurrentUser\\CA": "User Interm.CAs", "LocalMachine\\CA": "Mach. Interm.CAs",
        "CurrentUser\\AuthRoot": "User 3rd Party Roots", "LocalMachine\\AuthRoot": "Mach. 3rd Party Roots",
        "CurrentUser\\AddressBook": "User Contacts" # Other People
    }

    date_parser = None
    try:
        from dateutil import parser as dp
        date_parser = dp
    except ImportError:
        pass # Handled in parsing logic

    for store_path, store_friendly_name in cert_stores_map.items():
        command = [
            "powershell", "-NoProfile", "-NonInteractive", "-Command",
            f"Get-ChildItem -Path Cert:\\{store_path} -ErrorAction SilentlyContinue | "
            "Select-Object -Property Subject, Issuer, SerialNumber, Thumbprint, NotBefore, NotAfter, @{Name='StoreName';Expression={" + f"'{store_friendly_name}'" + "}} | "
            "ConvertTo-Json -Compress -Depth 3"
        ]
        try:
            process = subprocess.run(command, capture_output=True, text=True, check=False, encoding='utf-8', errors='ignore')
            if process.returncode != 0 and process.stderr:
                pass

            raw_json = process.stdout.strip()
            if not raw_json: continue

            certs_data = []
            if raw_json.startswith('[') and raw_json.endswith(']'):
                certs_data = json.loads(raw_json)
            elif raw_json.startswith('{') and raw_json.endswith('}'):
                certs_data = [json.loads(raw_json)]

            for cert_info in certs_data:
                valid_from_dt, valid_to_dt = None, None
                try:
                    if date_parser and cert_info.get("NotBefore"):
                        valid_from_dt = date_parser.parse(cert_info["NotBefore"])
                    elif cert_info.get("NotBefore"):
                        valid_from_dt = datetime.strptime(cert_info["NotBefore"].split('.')[0].split('+')[0].split('Z')[0], "%Y-%m-%dT%H:%M:%S")

                    if date_parser and cert_info.get("NotAfter"):
                        valid_to_dt = date_parser.parse(cert_info["NotAfter"])
                    elif cert_info.get("NotAfter"):
                        valid_to_dt = datetime.strptime(cert_info["NotAfter"].split('.')[0].split('+')[0].split('Z')[0], "%Y-%m-%dT%H:%M:%S")
                except Exception:
                    pass

                subject_str = cert_info.get("Subject", "N/A")
                issuer_str = cert_info.get("Issuer", "N/A")
                subject_cn = next((s.split('=')[1] for s in subject_str.split(', ') if s.startswith("CN=")), subject_str)
                issuer_cn = next((s.split('=')[1] for s in issuer_str.split(', ') if s.startswith("CN=")), issuer_str)

                results.append({
                    "subject_cn": subject_cn,
                    "issuer_cn": issuer_cn,
                    "serial_number": cert_info.get("SerialNumber", "N/A"),
                    "thumbprint_sha256": cert_info.get("Thumbprint", "N/A").lower(),
                    "valid_from": _format_datetime_obj(valid_from_dt) if valid_from_dt else "N/A",
                    "valid_to": _format_datetime_obj(valid_to_dt) if valid_to_dt else "N/A",
                    "source_detail": f"Win Store: {store_friendly_name}",
                    "raw_windows_info": cert_info
                })
        except FileNotFoundError:
            return [{"error": "PowerShell not found."}]
        except json.JSONDecodeError:
            continue
        except Exception:
            continue
    return results

def get_system_certificates_macos():
    results = []
    keychain_paths_config = [
        {"path": "/Library/Keychains/System.keychain", "label": "System Keychain"},
        {"path": os.path.expanduser("~/Library/Keychains/login.keychain-db"), "label": "Login Keychain"},
        {"path": "/System/Library/Keychains/SystemRootCertificates.keychain", "label": "System Roots"}
    ]

    login_alt = os.path.expanduser("~/Library/Keychains/login.keychain")
    if not os.path.exists(keychain_paths_config[1]["path"]) and os.path.exists(login_alt):
        keychain_paths_config[1]["path"] = login_alt

    for kc_info in keychain_paths_config:
        keychain_path = kc_info["path"]
        keychain_label = kc_info["label"]
        if not os.path.exists(keychain_path): continue

        command = ["security", "find-certificate", "-a", "-p", keychain_path]
        try:
            process = subprocess.run(command, capture_output=True, text=False, check=False)
            if process.returncode != 0: continue

            output_bytes = process.stdout
            pem_start_marker = b"-----BEGIN CERTIFICATE-----"
            pem_end_marker = b"-----END CERTIFICATE-----"

            current_pos = 0
            while current_pos < len(output_bytes):
                start_idx = output_bytes.find(pem_start_marker, current_pos)
                if start_idx == -1: break

                end_idx = output_bytes.find(pem_end_marker, start_idx)
                if end_idx == -1: break

                pem_block = output_bytes[start_idx : end_idx + len(pem_end_marker)]
                summary = _parse_pem_certificate_summary(pem_block, source_file_hint=keychain_label)
                if summary:
                    results.append(summary)
                current_pos = end_idx + len(pem_end_marker)
        except FileNotFoundError:
            return [{"error": "'security' command not found."}]
        except Exception:
            continue
    return results

def get_system_certificates_linux():
    results = []
    cert_sources = [
        {"path": "/etc/ssl/certs", "type": "dir", "label": "Sys SSL Certs Dir"},
        {"path": "/usr/local/share/ca-certificates", "type": "dir", "label": "User CA Certs"},
        {"path": "/etc/pki/tls/certs", "type": "dir", "label": "PKI TLS Certs Dir (RHEL)"},
        {"path": "/etc/ca-certificates/extracted", "type": "dir", "label": "Extracted CAs (Debian/Ubuntu)"},
        {"path": "/etc/ssl/certs/ca-certificates.crt", "type": "bundle", "label": "Main CA Bundle"},
        {"path": os.path.expanduser("~/.local/share/ca-certificates"), "type":"dir", "label": "User Local CA Certs"}
    ]

    processed_fingerprints = set()

    for source in cert_sources:
        path_item = source["path"]
        source_label = source["label"]
        if not os.path.exists(path_item): continue

        if source["type"] == "bundle" and os.path.isfile(path_item):
            try:
                with open(path_item, "rb") as f: file_content_bytes = f.read()

                pem_start_marker = b"-----BEGIN CERTIFICATE-----"
                pem_end_marker = b"-----END CERTIFICATE-----"
                current_pos = 0
                while current_pos < len(file_content_bytes):
                    start_idx = file_content_bytes.find(pem_start_marker, current_pos)
                    if start_idx == -1: break
                    end_idx = file_content_bytes.find(pem_end_marker, start_idx)
                    if end_idx == -1: break

                    pem_block = file_content_bytes[start_idx : end_idx + len(pem_end_marker)]
                    summary = _parse_pem_certificate_summary(pem_block, source_file_hint=f"{source_label} (Bundle)")
                    if summary:
                        thumbprint = summary.get("thumbprint_sha256")
                        if thumbprint not in processed_fingerprints:
                            results.append(summary)
                            processed_fingerprints.add(thumbprint)
                    current_pos = end_idx + len(pem_end_marker)
            except Exception:
                continue

        elif source["type"] == "dir" and os.path.isdir(path_item):
            try:
                for filename in os.listdir(path_item):
                    filepath = os.path.join(path_item, filename)
                    if os.path.isfile(filepath) and (filename.endswith((".pem", ".crt", ".cer")) or os.path.islink(filepath)):
                        try:
                            with open(filepath, "rb") as f: cert_data_bytes = f.read()
                            summary = _parse_pem_certificate_summary(cert_data_bytes, source_file_hint=f"{source_label} File: {filename}")
                            if summary:
                                thumbprint = summary.get("thumbprint_sha256")
                                if thumbprint not in processed_fingerprints:
                                    results.append(summary)
                                    processed_fingerprints.add(thumbprint)
                        except Exception:
                            continue
            except Exception:
                continue
    return results

def get_system_certificates():
    os_name = platform.system().lower()
    if os_name == "windows":
        return get_system_certificates_windows()
    elif os_name == "darwin":
        return get_system_certificates_macos()
    elif os_name == "linux":
        return get_system_certificates_linux()
    else:
        return [{"error": f"OS '{platform.system()}' not supported for cert store exam."}]

if __name__ == '__main__':
    print(f"Certificate Store Scan for: {platform.system()}")
    certs = get_system_certificates()
    limit = 10

    if certs and isinstance(certs, list) and certs[0].get("error"):
        print(f"Error: {certs[0]['error']}")
    elif not certs:
        print("No certificates found or an issue occurred.")
    else:
        print(f"Found {len(certs)} certificates (showing up to {limit}):")
        for i, cert_summary in enumerate(certs):
            if i >= limit:
                print(f"... and {len(certs) - limit} more.")
                break
            print("-" * 20)
            print(f"  Subject:    {cert_summary.get('subject_cn', 'N/A')}")
            print(f"  Issuer:     {cert_summary.get('issuer_cn', 'N/A')}")
            print(f"  Serial:     {cert_summary.get('serial_number', 'N/A')}")
            print(f"  Thumbprint: {cert_summary.get('thumbprint_sha256', 'N/A')}")
            print(f"  Valid To:   {cert_summary.get('valid_to', 'N/A')}")
            print(f"  Source:     {cert_summary.get('source_detail', 'N/A')}")
            if "pem_data" in cert_summary and cert_summary["pem_data"]:
                 print(f"  PEM:        Yes ({len(cert_summary['pem_data'])} chars)")
            # if "raw_windows_info" in cert_summary: (Example for platform specific)
            #      pass
