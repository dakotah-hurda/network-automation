import pynetbox

class DataError(Exception):
    """This custom error class allows you to add data to raised Errors for additional
    processing in the adjacent error_reporting module.
    """
    def __init__(self, message, 
            error_type: str = "", 
            device: pynetbox.models.dcim.Devices = {}, 
            extra_data: dict = {}
            ):
        """Used to package base_compliancy module errors for error_reporting module

        Args:
            message (str): Nominal error message
            error_type (str, optional): Type of error used for parsing. Defaults to empty string.
            device_data (pynetbox.models.dcim.Devices, optional): Netbox device object from pynetbox. Defaults to empty dict.
            extra_data (dict, optional): Arbitrary additional data. Defaults to empty dict.
        """
        super().__init__(message)
        self.error_type = error_type
        self.device = device
        self.extra_data = extra_data

# collect_nb_devices custom errors
class SNMPError(Exception):
    pass

# snmp_utils custom errors
class SNMPError(Exception):
    pass

class RequestTimedOutError(SNMPError):
    pass

class WrongSNMPDigest(SNMPError):
    pass

class WrongSNMPOid(SNMPError):
    pass

class OtherSNMPError(SNMPError):
    pass