def log_parser(DataError):
    """Receives custom DataError objects and routes error-logging requests to the correct
    reporter function in this module.

    Args:
        DataError: Custom error with extra data attributes from adjacent custom_errors module.

    Raises:
        ValueError: Alerts if received error_type unfound in the error_types dict.
    """
    
    # Maps error_types to correct reporter(s). Change value to 'list' for multiple reporters.
    error_types = {
        
        # Generic
        '': 'api_reporter',

        # Misc Errors
        'NetboxCompliancy': 'api_reporter',

        # SNMP Issues
        'SNMPTimeout': 'api_reporter',
        'SNMPBadDigest': 'api_reporter',
        'SNMPBadOID': 'api_reporter',
        'OtherSNMPError': 'api_reporter',
        
        # Missing Data Types
        'MissingDataIPv4': 'api_reporter',
        'MissingDataSerialNumber': 'api_reporter',
        'MissingDataHostname': 'api_reporter',
        'MissingDataDeviceType': 'api_reporter', 
        'MissingDataPlatform': 'api_reporter',

        # Data-comparison Types
        'SerialNumberMismatch': 'api_reporter',
        'HostnameMismatch': 'api_reporter', 
        'HardwareModelMismatch': 'api_reporter', 
        'SoftwareVersionMismatch': 'api_reporter', 
        'LongUptime': 'api_reporter', 
    }
    
    try: reporter_function = globals()[error_types[DataError.error_type]]
    
    # Catches undefined error_types being passed to this func
    except KeyError as e: 
        raise ValueError(f"Unregistered error_type passed to log_parser func: '{DataError.error_type}'")
    
    reporter_function(DataError)

def api_reporter(DataError):
    """Function to report normalized data to defined API endpoint. 
    This function should NOT be called directly. Use the adjacent log_parser function.

    Args:
        DataError: Custom error with extra data attributes from adjacent custom_errors module.
    """
    print("*" * 80)
    print(f"Executing API error reporter:\n\n{DataError}")
    print(f"ERROR_TYPE: {DataError.error_type}")
    print(f"DEVICE: {DataError.device}")
    print(f"EXTRA DATA: {DataError.extra_data}")
    print("*" * 80)

def smtp_reporter(DataError):
    """Function to report normalized data to defined email address.
    This function should NOT be called directly. Use the adjacent log_parser function.

    Args:
        DataError: Custom error with extra data attributes from adjacent custom_errors module.
    """
    print(f"Executing SMTP error reporter:\n\n{DataError}")

def snmp_reporter(DataError):
    """Function to report normalized data to defined SNMP receiver. 
    This function should NOT be called directly. Use the adjacent log_parser function.

    Args:
        DataError: Custom error with extra data attributes from adjacent custom_errors module.
    """
    print(f"Executing SNMP error reporter:\n\n{DataError}")

def syslog_reporter(DataError):
    """Function to report normalized data to defined Syslog receiver. 
    This function should NOT be called directly. Use the adjacent log_parser function.

    Args:
        DataError: Custom error with extra data attributes from adjacent custom_errors module.
    """
    print(f"Executing Syslog error reporter:\n\n{DataError}")