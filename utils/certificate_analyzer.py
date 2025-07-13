import datetime
from cryptography import x509
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import dsa, ec, rsa
# Removed unused serialization imports: load_pem_private_key, etc.
from cryptography.x509.oid import NameOID, ExtendedKeyUsageOID, AuthorityInformationAccessOID
from cryptography.hazmat.backends import default_backend
import os # For file operations in main example (if any)

def _format_name(name_obj):
    """Formats an X509 Name object into a readable string."""
    if not name_obj:
        return "N/A"

    # If name_obj is a single NameAttribute, format it directly.
    # This handles potential misuse by a caller or an unexpected structure.
    if isinstance(name_obj, x509.NameAttribute):
        try:
            return f"{name_obj.oid._name}={name_obj.value}"
        except Exception as e:
            return f"Error formatting NameAttribute: {e}"

    # Proceed if name_obj is an x509.Name (which is an RDNSequence)
    if not isinstance(name_obj, x509.Name):
        return f"Unsupported name type: {type(name_obj)}"

    parts = []
    try:
        for rdn in name_obj:  # rdn is x509.RelativeDistinguishedName
            # Ensure rdn is iterable (it should be a frozenset of NameAttributes)
            if not hasattr(rdn, '__iter__'):
                # This case is unlikely given cryptography's types but defensive.
                if isinstance(rdn, x509.NameAttribute): # If an RDNSequence contains a raw NameAttribute
                     parts.append(f"{rdn.oid._name}={rdn.value}")
                else:
                     parts.append(f"Uniterable RDN component: {type(rdn)}")
                continue

            for attr in rdn:  # attr is x509.NameAttribute
                if isinstance(attr, x509.NameAttribute):
                    parts.append(f"{attr.oid._name}={attr.value}")
                else:
                    # This case should not occur if rdn contains only NameAttributes
                    parts.append(f"Unknown attribute type in RDN: {type(attr)}")
    except Exception as e:
        # Catch any other unexpected error during iteration
        return f"Error formatting name components: {e}"

    if not parts: # If the name was valid but had no recognizable attributes
        try:
            return name_obj.rfc4514_string() # Fallback to RFC4514 string if parts list is empty
        except Exception:
            return "Empty or unparseable name"

    return ", ".join(parts)

def _format_datetime(dt_obj):
    """Formats a datetime object into a readable string, assuming UTC if naive."""
    if dt_obj is None:
        return "N/A"
    # cryptography's not_valid_before/after are naive but represent UTC.
    # Make them timezone-aware for correct strftime %Z behavior.
    if dt_obj.tzinfo is None:
        import datetime as dt_module # Ensure full datetime module for timezone
        dt_obj = dt_obj.replace(tzinfo=dt_module.timezone.utc)
    return dt_obj.strftime("%Y-%m-%d %H:%M:%S %Z")


def _get_extension_value(certificate, oid):
    """Safely retrieves an extension value by OID."""
    try:
        ext = certificate.extensions.get_extension_for_oid(oid)
        return ext.value
    except x509.ExtensionNotFound:
        return None
    except Exception: # Catch any other error during extension access
        return None

def _parse_certificate_object(cert):
    """Helper function to parse a cryptography.x509.Certificate object."""
    details = {}

    details["Subject"] = _format_name(cert.subject)
    subject_cn_attrs = cert.subject.get_attributes_for_oid(NameOID.COMMON_NAME)
    details["Subject CN"] = subject_cn_attrs[0].value if subject_cn_attrs else "N/A"

    details["Issuer"] = _format_name(cert.issuer)
    issuer_cn_attrs = cert.issuer.get_attributes_for_oid(NameOID.COMMON_NAME)
    details["Issuer CN"] = issuer_cn_attrs[0].value if issuer_cn_attrs else "N/A"

    # Use _utc versions if available (cryptography >= 38.0.0), else fallback
    valid_from = cert.not_valid_before_utc if hasattr(cert, 'not_valid_before_utc') else cert.not_valid_before
    valid_to = cert.not_valid_after_utc if hasattr(cert, 'not_valid_after_utc') else cert.not_valid_after
    details["Valid From"] = _format_datetime(valid_from)
    details["Valid To"] = _format_datetime(valid_to)

    details["Serial Number"] = cert.serial_number.to_bytes((cert.serial_number.bit_length() + 7) // 8, 'big').hex(':')

    details["Signature Algorithm"] = cert.signature_algorithm_oid._name if cert.signature_algorithm_oid else "N/A"

    public_key = cert.public_key()
    key_info = {}
    if isinstance(public_key, rsa.RSAPublicKey):
        key_info["Algorithm"] = "RSA"
        key_info["Key Size (bits)"] = public_key.key_size
    elif isinstance(public_key, dsa.DSAPublicKey):
        key_info["Algorithm"] = "DSA"
        key_info["Key Size (bits)"] = public_key.key_size
    elif isinstance(public_key, ec.EllipticCurvePublicKey):
        key_info["Algorithm"] = "ECC"
        key_info["Curve"] = public_key.curve.name if public_key.curve else "N/A"
        key_info["Key Size (bits)"] = public_key.key_size
    else:
        key_info["Algorithm"] = "Unknown"
    details["Public Key Info"] = key_info

    bc_ext = _get_extension_value(cert, x509.oid.ExtensionOID.BASIC_CONSTRAINTS)
    if bc_ext:
        details["Basic Constraints"] = {
            "Is CA": bc_ext.ca,
            "Path Length Constraint": bc_ext.path_length if bc_ext.path_length is not None else "None"
        }
    else:
        details["Basic Constraints"] = "Not Present"

    ku_ext = _get_extension_value(cert, x509.oid.ExtensionOID.KEY_USAGE)
    if ku_ext:
        key_usage = []
        if ku_ext.digital_signature: key_usage.append("Digital Signature")
        if ku_ext.content_commitment: key_usage.append("Content Commitment") # aka nonRepudiation
        if ku_ext.key_encipherment: key_usage.append("Key Encipherment")
        if ku_ext.data_encipherment: key_usage.append("Data Encipherment")
        if ku_ext.key_agreement: key_usage.append("Key Agreement")
        if ku_ext.key_cert_sign: key_usage.append("Certificate Sign")
        if ku_ext.crl_sign: key_usage.append("CRL Sign")
        if hasattr(ku_ext, 'encipher_only') and ku_ext.encipher_only and ku_ext.key_agreement: key_usage.append("Encipher Only")
        if hasattr(ku_ext, 'decipher_only') and ku_ext.decipher_only and ku_ext.key_agreement: key_usage.append("Decipher Only")
        details["Key Usage"] = ", ".join(key_usage) if key_usage else "Not Specified"
    else:
        details["Key Usage"] = "Not Present"

    eku_ext = _get_extension_value(cert, x509.oid.ExtensionOID.EXTENDED_KEY_USAGE)
    if eku_ext:
        extended_key_usage = [oid._name for oid in eku_ext if hasattr(oid, '_name')]
        details["Extended Key Usage"] = ", ".join(extended_key_usage) if extended_key_usage else "Not Specified"
    else:
        details["Extended Key Usage"] = "Not Present"

    san_ext = _get_extension_value(cert, x509.oid.ExtensionOID.SUBJECT_ALTERNATIVE_NAME)
    sans = []
    if san_ext:
        for general_name in san_ext:
            if isinstance(general_name, x509.DNSName):
                sans.append(f"DNS: {general_name.value}")
            elif isinstance(general_name, x509.IPAddress):
                sans.append(f"IP: {str(general_name.value)}") # Ensure IPAddress is string
            elif isinstance(general_name, x509.DirectoryName):
                sans.append(f"DN: {_format_name(general_name.value)}")
            elif isinstance(general_name, x509.RFC822Name):
                sans.append(f"Email: {general_name.value}")
            elif isinstance(general_name, x509.UniformResourceIdentifier):
                sans.append(f"URI: {general_name.value}")
        details["Subject Alternative Names"] = sans if sans else ["Not Present"]
    else:
        details["Subject Alternative Names"] = ["Not Present"]

    details["Fingerprints"] = {
        "SHA-1": cert.fingerprint(hashes.SHA1()).hex(':'),
        "SHA-256": cert.fingerprint(hashes.SHA256()).hex(':')
    }

    aia_ext = _get_extension_value(cert, x509.oid.ExtensionOID.AUTHORITY_INFORMATION_ACCESS)
    aia_info = {}
    if aia_ext:
        for desc in aia_ext:
            access_method_name = desc.access_method._name if hasattr(desc.access_method, '_name') else str(desc.access_method.dotted_string)
            access_location_value = desc.access_location.value if hasattr(desc.access_location, 'value') else str(desc.access_location)

            if desc.access_method == AuthorityInformationAccessOID.CA_ISSUERS:
                aia_info["CA Issuers URI"] = access_location_value
            elif desc.access_method == AuthorityInformationAccessOID.OCSP:
                 aia_info["OCSP Server URI"] = access_location_value
            else: # Generic display for other AIAs
                aia_info[f"{access_method_name}"] = access_location_value
        details["Authority Information Access"] = aia_info if aia_info else "Not Present"
    else:
        details["Authority Information Access"] = "Not Present"

    ski_ext = _get_extension_value(cert, x509.oid.ExtensionOID.SUBJECT_KEY_IDENTIFIER)
    if ski_ext:
        details["Subject Key Identifier"] = ski_ext.digest.hex(':')
    else:
        details["Subject Key Identifier"] = "Not Present"

    aki_ext = _get_extension_value(cert, x509.oid.ExtensionOID.AUTHORITY_KEY_IDENTIFIER)
    if aki_ext:
        aki_details = {}
        if aki_ext.key_identifier:
            aki_details["Key Identifier"] = aki_ext.key_identifier.hex(':')
        if aki_ext.authority_cert_issuer:
            aki_details["Authority Cert Issuer"] = [_format_name(name) for name in aki_ext.authority_cert_issuer]
        if aki_ext.authority_cert_serial_number:
            aki_details["Authority Cert Serial Number"] = hex(aki_ext.authority_cert_serial_number)
        details["Authority Key Identifier"] = aki_details if aki_details else "Not Present"
    else:
        details["Authority Key Identifier"] = "Not Present"

    return details

def analyze_certificate_data(cert_data_bytes):
    """
    Analyzes certificate data provided as bytes.
    Supports PEM and DER encoded certificates.
    Returns a dictionary of details or an error dictionary.
    """
    cert = None
    error_log = []

    # Try loading as PEM
    try:
        cert = x509.load_pem_x509_certificate(cert_data_bytes, default_backend())
    except ValueError:
        error_log.append("Failed to load as PEM.")
        # Try loading as DER
        try:
            cert = x509.load_der_x509_certificate(cert_data_bytes, default_backend())
        except ValueError:
            error_log.append("Failed to load as DER.")
            return {"error": "Could not parse certificate. " + " ".join(error_log)}
        except Exception as e_der:
            error_log.append(f"General error loading as DER: {e_der}")
            return {"error": "Could not parse certificate. " + " ".join(error_log)}
    except Exception as e_pem:
        error_log.append(f"General error loading as PEM: {e_pem}")
        return {"error": "Could not parse certificate. " + " ".join(error_log)}

    if not cert: # Should be caught by above, but as a safeguard
        return {"error": "Unsupported certificate format or corrupted data. " + " ".join(error_log)}

    return _parse_certificate_object(cert)


def analyze_certificate(file_path):
    """
    Analyzes a certificate file and returns a dictionary of its details.
    Supports PEM and DER encoded certificates.
    """
    try:
        with open(file_path, "rb") as f:
            cert_data = f.read()
    except IOError as e:
        return {"error": f"Could not read file: {e}"}

    return analyze_certificate_data(cert_data)


def format_certificate_details(details):
    """Formats the certificate details dictionary into a readable string."""
    if not details or "error" in details:
        return f"Error: {details.get('error', 'Unknown error processing certificate details.')}"

    output = []
    output.append("Certificate Analysis:")
    output.append("=====================")

    def append_detail(label, value, indent=1):
        prefix = "  " * indent
        if isinstance(value, dict):
            output.append(f"{prefix}{label}:")
            for k, v in value.items():
                append_detail(k, v, indent + 1)
        elif isinstance(value, list):
            if not value: # Handle empty list
                 output.append(f"{prefix}{label}: Not Present")
                 return
            output.append(f"{prefix}{label}:")
            all_not_present = True
            for item in value:
                if item != "Not Present": # Check if at least one item is not "Not Present"
                    all_not_present = False
                    break
            if all_not_present and value == ["Not Present"]: # Only if it's explicitly ["Not Present"]
                 output.append(f"{prefix}  Not Present")
                 return

            for item in value:
                if isinstance(item, str): # and item != "Not Present" (already handled by all_not_present logic for the list itself)
                     output.append(f"{prefix}  - {item}")
                # elif item != "Not Present": # Could be other types, let str() handle them
                else:
                     output.append(f"{prefix}  - {str(item)}")

        elif value is not None and value != "N/A" and value != "Not Present":
            output.append(f"{prefix}{label}: {value}")
        else: # Handle N/A or Not Present explicitly for consistent output
            output.append(f"{prefix}{label}: {value if value is not None else 'N/A'}")


    append_detail("Subject", details.get('Subject'))
    append_detail("Issuer", details.get('Issuer'))
    append_detail("Serial Number", details.get('Serial Number'))
    append_detail("Version", "3 (Implicit X.509v3)")

    output.append("\n[Validity Period]")
    append_detail("Not Valid Before", details.get('Valid From'))
    append_detail("Not Valid After", details.get('Valid To'))

    output.append("\n[Public Key Information]")
    pk_info = details.get('Public Key Info', {})
    append_detail("Algorithm", pk_info.get('Algorithm'))
    if 'Key Size (bits)' in pk_info: append_detail("Key Size", f"{pk_info.get('Key Size (bits)')} bits")
    if 'Curve' in pk_info: append_detail("Curve", pk_info.get('Curve'))

    output.append("\n[Signature Information]")
    append_detail("Signature Algorithm", details.get('Signature Algorithm'))

    output.append("\n[X.509 v3 Extensions]")
    append_detail("Basic Constraints", details.get("Basic Constraints"))
    append_detail("Key Usage", details.get('Key Usage'))
    append_detail("Extended Key Usage", details.get('Extended Key Usage'))
    append_detail("Subject Alternative Names (SANs)", details.get("Subject Alternative Names"))
    append_detail("Subject Key Identifier", details.get('Subject Key Identifier'))
    append_detail("Authority Key Identifier", details.get('Authority Key Identifier'))
    append_detail("Authority Information Access (AIA)", details.get("Authority Information Access"))

    output.append("\n[Fingerprints]")
    fingerprints = details.get('Fingerprints', {})
    append_detail("SHA-256", fingerprints.get('SHA-256'))
    append_detail("SHA-1", fingerprints.get('SHA-1'))

    return "\n".join(output)

if __name__ == '__main__':
    print("Certificate Analyzer Utility")
    print("--------------------------")

    # Test with a dummy non-existent file
    error_result = analyze_certificate("non_existent_file.pem")
    print("\n--- Test: Non-existent file ---")
    print(format_certificate_details(error_result))

    # Test with dummy non-certificate data (bytes)
    dummy_data_bytes = b"This is not a certificate."
    error_result_data = analyze_certificate_data(dummy_data_bytes)
    print("\n--- Test: Non-certificate data (bytes) ---")
    print(format_certificate_details(error_result_data))

    # Test with a self-signed PEM cert string (replace with a real one for actual testing)
    sample_pem_bytes = (
        b"-----BEGIN CERTIFICATE-----\n"
        b"MIIC/jCCAeagAwIBAgIJAP44T9u9CMB9MA0GCSqGSIb3DQEBCwUAMBMxETAPBgNV\n"
        b"BAMMCGxvY2FsaG9zdDAeFw0yMDAxMDEwMDAwMDBaFw0zMDAxMDEwMDAwMDBaMBMx\n"
        b"ETAPBgNVBAMMCGxvY2FsaG9zdDCCASIwDQYJKoZIhvcNAQEBBQADggEPADCCAQoC\n"
        b"ggEBALM+rS56j7a0HSW0skP3YJk4pEgNlhKggO9wZ0SqeZJzIEgRQz13j5g4G0gc\n"
        b"uMLvR2Z2lwMGsTBIYc/n849+J2MZ9N4fT/TR2KVXgwNOXwYTGNHc2y09kT82961k\n"
        b"i0A//2gCVc7UIAlkYpPz68himNe9rQ71qFChA5XKnKAP8jFxPbAM2rAGu3003+z3\n"
        b"rO7LwzIUD9bW30nicqmFL/uQ57ja0IODwXjB6G3uD497ZDNn8hNnb8O7hb07w0sY\n"
        b"jPgjxn2gIf1PjMRXiu9aD0AnrVxZ8XjKiLCxeLDYg4h6SgP8kLW8COx1PjY3R/sC\n"
        b"AwEAAaNTMFEwHQYDVR0OBBYEFPHr4C7uJ68NJP474TIMPS2o310wMB8GA1UdIwQY\n"
        b"MBaAFPHr4C7uJ68NJP474TIMPS2o310wMA8GA1UdEwEB/wQFMAMBAf8wDQYJKoZI\n"
        b"hvcNAQELBQADggEBAIgY47Z1gsN1p05nXLylxwqYt6hH07xAXsrpF3WIss0T70HM\n"
        b"2C2BQXEHz8OCPs6tepYTO0tL8v0zXDnerekWaSqd8LhJDT1tf008xZhbQ5d4ddLT\n"
        b"VbEa0pE5bUXQnIs5QRAHqRpzBybUYf5pMXdU2sD5k7vq7j4YjzY+M2rO0LVDh2Vy\n"
        b"7Nf7AnOLLXDwBkXsbxoD8o3i5xHGyT7gBt4ojG10k8f9sLpIXqNLYxWVj7gYfL/B\n"
        b"ZChQIjR283n5h9sXDZQGgPzV7f6m9bF9d3P2e7K9F8a3z9K2B+J2c2e0c5Y5ff6/\n"
        b"8W0L9Lw=\n"
        b"-----END CERTIFICATE-----\n"
    )
    print("\n--- Test: Sample PEM data (bytes) ---")
    # This sample PEM is minimal, from an old test. `cryptography` might be strict.
    # It's better to use a cert known to be valid for a full test.
    # For now, this demonstrates the data pathway.
    analysis_result_data_pem = analyze_certificate_data(sample_pem_bytes)
    print(format_certificate_details(analysis_result_data_pem))

    print("\nUsage: \n  analyze_certificate(file_path) -> dict")
    print("  analyze_certificate_data(bytes_data) -> dict")
    print("  format_certificate_details(dict_result) -> str")
