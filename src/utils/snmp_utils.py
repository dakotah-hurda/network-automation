# Standard Library
import os
from pprint import pprint 

# Non-Standard Library
from dotenv import load_dotenv
import pysnmp
from pysnmp.hlapi import *

# Custom imports
import error_handling.custom_errors as err

def get_snmp_data(target_host: str, oid: str) -> str:
    """Basic SNMP function that collects the given OID from the given IP address.

    Args:
        target_host (str): IP address of the host you want to query.
        oid (str): Full OID you want to collect. 

    Returns:
        str: OID value. 
    """
    
    load_dotenv()

    snmp_engine = SnmpEngine()
    snmp_user = UsmUserData(
        userName=os.getenv("snmp_user"),
        authKey=os.getenv("snmp_auth"),
        privKey=os.getenv("snmp_priv"),
        authProtocol=usmHMACSHAAuthProtocol,
        privProtocol=usmAesCfb128Protocol,
    )
    
    # Create SNMP request
    error_indication, error_status, error_index, var_binds = next(
        getCmd(
            snmp_engine,
            snmp_user,
            UdpTransportTarget((target_host, 161)),
            ContextData(),
            ObjectType(ObjectIdentity(oid)),
        )
    )

    # This print is helpful for figuring out the var_binds obj_types below.
    # https://pysnmp.readthedocs.io/en/latest/docs/api-reference.html#pysnmp.proto.rfc1902.OctetString
    # print(type(var_binds[0][1]))

    # Check for errors
    if isinstance(error_indication, pysnmp.proto.errind.RequestTimedOut):
        raise err.RequestTimedOutError("SNMP request timed out")
    if isinstance(error_indication, pysnmp.proto.errind.WrongDigest):
        raise err.WrongSNMPDigest("SNMP Digest incorrect - possibly incorrect credentials")
    if isinstance(var_binds[0][1], pysnmp.proto.rfc1905.NoSuchObject) or isinstance(var_binds[0][1], pysnmp.proto.rfc1905.NoSuchInstance):
        raise err.WrongSNMPOid("Incorrect OID passed to device")
    
    # Extract and return the result
    if isinstance(var_binds[0][1], pysnmp.proto.rfc1902.OctetString) or isinstance(var_binds[0][1], pysnmp.proto.rfc1902.TimeTicks):
        return str(var_binds[0][1]) # pysnmp.proto.rfc1902.OctetString
    else:
        print(type(var_binds[0][1]))
        raise err.OtherSNMPError("Unknown SNMP error, see snmp_utils.py")