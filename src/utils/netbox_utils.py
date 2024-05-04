from dotenv import load_dotenv
import os
import pynetbox
import requests


def get_api_token(
    username: str,
    password: str,
    url: str = "https://netbox.mke.cnty",
) -> str:
    """Generates API token for provided Admin credentials.

    Args:
        username (str): Admin username to generate API token for.
        password (str): Corresponding admin password.
        url (str, optional): Netbox URL endpoint to retrieve token from. Defaults to "https://netbox.mke.cnty".

    Returns:
        str: Cleartext token string.
    """

    nb_conn = pynetbox.api(url=url)

    token = nb_conn.create_token(username=username, password=password)

    return str(token.key)


def get_devicetype_oids(
    device_type: str, api_token:str, url: str = "https://netbox.mke.cnty"
) -> dict:
    """Retrieves all relevant SNMP OIDs for the given device_type from Netbox.

    Args:
        device_type (str): Device_type 'model' field from Netbox API documentation (dcim/device-types)
        api_token (str): Netbox API Token
        url (str, optional): Netbox URL. Defaults to "https://netbox.mke.cnty".

    Returns:
        dict: Returns a dict of all SNMP OIDs configured for the device_type on Netbox.
    """

    nb = pynetbox.api(url=url, token=api_token)

    device_type_data = nb.dcim.device_types.get(model=device_type)

    snmp_oids = {
        "snmp_hwmodel_oid": device_type_data.custom_fields.get("snmp_hwmodel_oid"),
        "snmp_sn_oid": device_type_data.custom_fields.get("snmp_sn_oid"),
        "snmp_swversion_oid": device_type_data.custom_fields.get("snmp_swversion_oid"),
        "snmp_sysname_oid": device_type_data.custom_fields.get("snmp_sysname_oid"),
        "snmp_sysuptime_oid": device_type_data.custom_fields.get("snmp_sysuptime_oid"),
    }

    try:
        # Check if all values are not None
        check_oid_existence = all(value is not None for value in snmp_oids.values())
        assert check_oid_existence, f"Missing OIDs for {device_type}"
        return snmp_oids
    
    except AssertionError as e:
        print(f"ERROR: Some SNMP OID values are missing for provide device_type: {device_type}")
        raise
