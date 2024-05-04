# Standard Library
import argparse
import os
import sys

# Non-Standard Library
from dotenv import load_dotenv
import pynetbox

# Custom imports
import error_handling.custom_errors as err
import error_handling.error_reporting as err_report
from utils import snmp_utils, netbox_utils


def main(url, api_token):
    
    # Collect data from Netbox
    try: nb_devices = collect_nb_devices(url=url, api_token=api_token)
    except err.DataError as e:
        err_report.log_parser(e)
        sys.exit(1)
    except Exception as e:
        raise (e)

    for device in nb_devices:
        if device.name == "test-sw01" or device.name == "test-sw02":  # filtering output for testing
            
            # Pre-checks that the NB data is good.
            try: test_nb_data(device)
            except err.DataError as e:
                err_report.log_parser(e)
                continue
            except Exception as e:
                raise (e)

            # Collect live data from device.
            try: live_data = gather_live_data(device, api_token, url)
            except err.DataError as e:
                err_report.log_parser(e)
                continue
            except Exception as e:
                raise (e)

            # Compare netbox data with live data
            try: compare_data(device=device, live_data=live_data)
            except err.DataError as e:
                err_report.log_parser(e)
                continue
            except Exception as e:
                raise (e)

        else:
            continue

def collect_nb_devices(url: str, api_token: str) -> list:
    # Initialize NetBox API
    nb = pynetbox.api(url=url, token=api_token)

    # Static vars
    nb_role_searchlist = [
        "sw",
        # "ag",
        # "cr",
        # "ds",
        # "fw",
        # "rt",
    ]

    # for role in nb_role_searchlist:
    try: 
        nb_devices = nb.dcim.devices.filter(status='active', role=nb_role_searchlist)
        return nb_devices
    except pynetbox.core.query.ContentError as e:
        error_message = f"ERROR: Incorrect Netbox URL passed to collect_nb_devices function."
        raise err.DataError(message=error_message,extra_data={'original_exception': e})
    except pynetbox.core.query.RequestError as e:
        error_message = f"ERROR: Netbox Request error."
        raise err.DataError(message=error_message,extra_data={'original_exception': e})

def test_nb_data(device: pynetbox.models.dcim.Devices):
    """Tests that the provided device has all the critical pieces of data needed in Netbox.

    Args:
        device (pynetbox.models.dcim.Devices): Netbox device object from pynetbox

    Raises:
        err.MissingPrimaryIPv4Address: Error used to report that the device is missing a Primary IPv4 Address in Netbox
        err.MissingSerialNumber: Error used to report that the device is missing a Serial Number in Netbox
        err.MissingHostname: Error used to report that the device is missing a Hostname in Netbox
        err.MissingDeviceType: Error used to report that the device is missing a DeviceType (hardware model) in Netbox
        err.MissingPlatform: Error used to report that the device is missing a Platform (software version) in Netbox

    Returns:
        bool: Returns True if all checks succeed.
    """

    try:
        assert device.primary_ip4 is not None
    except AssertionError:
        error_message = f"ERROR: {device.name} is missing a primary IPv4 Address."
        raise err.DataError(message=error_message, error_type="MissingDataIPv4", device=device)

    try:
        assert device.serial is not None
    except AssertionError:
        error_message = f"ERROR: {device.name} is missing a Serial Number."
        raise err.DataError(message=error_message, error_type="MissingDataSerialNumber", device=device)

    try:
        assert device.name is not None
    except AssertionError:
        error_message = f"ERROR: {device.name} is missing a hostname."
        raise err.DataError(message=error_message, error_type="MissingDataHostname", device=device)

    try:
        assert device.device_type is not None
    except AssertionError:
        error_message = f"ERROR: {device.name} is missing a device_type."
        raise err.DataError(message=error_message, error_type="MissingDataDeviceType", device=device)

    try:
        assert device.platform is not None
    except AssertionError:
        error_message = f"ERROR: {device.name} is missing a platform."
        raise err.DataError(message=error_message, error_type="MissingDataPlatform", device=device)

def gather_live_data(device, api_token, url) -> dict:
    """Handler function for collecting live data from the provided device.
    Calls more discrete functions to collect data via provided method.

    Default method is SNMPv3, but functionality can be added for API, SNMP, etc.

    Args:
        device: Device object returned by querying Netbox via pynetbox.

    Returns:
        dict: Dictionary of relevant live data values for comparison
    """
    
    device_ip = str(device.primary_ip4).split("/")[0]  # remove CIDR from NB
    oids = netbox_utils.get_devicetype_oids(
        device_type=device.device_type, api_token=api_token, url=url
    )  # get OIDs from NB

    
    live_data = {}

    # Maps snmp_oids to script vars
    snmp_data_mapping = {
    "serial_number": oids["snmp_sn_oid"],
    "system_name": oids["snmp_sysname_oid"],
    "hardware_model": oids["snmp_hwmodel_oid"],
    "sw_version": oids["snmp_swversion_oid"],
    "sys_uptime": oids["snmp_sysuptime_oid"]
    }

    # Collecting SNMP Data by submitting OIDs found in Netbox
    for key, oid in snmp_data_mapping.items():
        try:
            # retrieve snmp data
            data = snmp_utils.get_snmp_data(device_ip, oid)
            
            # formatting keys
            if key == "system_name":
                data = data.split(".")[0].strip()
            elif key == "sys_uptime":
                data = int(data) if data else 0

            # organizing collected data
            live_data[key] = data.strip() if isinstance(data, str) else data
        
        except err.RequestTimedOutError:
            error_message = f"ERROR: {device} - SNMP Timeout, check connectivity"
            raise err.DataError(message=error_message, error_type="SNMPTimeout", device=device)
        
        except err.WrongSNMPDigest:
            error_message = f"ERROR: {device} - SNMP Wrong Digest, check credentials"
            raise err.DataError(message=error_message, error_type="SNMPBadDigest", device=device)
        
        except err.WrongSNMPOid:
            error_message = f"ERROR: {device} - No such OID at device, check for incorrect OID"
            raise err.DataError(message=error_message, error_type="SNMPBadOID", device=device, extra_data={'sent_oid': oid, 'nb_dvc_type': device.device_type})
        
        except err.OtherSNMPError:
            error_message = f"ERROR: {device} - Unknown SNMP error encountered. "
            raise err.DataError(message=error_message, error_type="OtherSNMPError", device=device, extra_data={'sent_oid': oid, 'nb_dvc_type': device.device_type})
        
        except Exception as e:
            raise(e)

    # Printing SNMP results
    print("*" * 80)
    for key, value in live_data.items():
        print(f"{key}: {value}")
    print("*" * 80)
    return live_data

def compare_data(device: pynetbox.models.dcim.Devices, live_data: dict):
    """Compares the retrieved Netbox data with retrieved "live" data.

    Args:
        device (pynetbox.models.dcim.Devices): Netbox device object from pynetbox
        live_data (dict): Dictionary representing data collected via SNMP

    Raises:
        err.SerialMatchError: Error used for alerting when serial numbers don't match
        err.HostnameMatchError: Error used for alerting when hostnames don't match
        err.HardwareModelMatchError: Error used for alerting when hardware models don't match
        err.SoftwareVersionMatchError: Error used for alerting when software versions don't match
        err.LongUptimeError: Error used for alerting when uptime is longer than 1 year

    Returns:
        bool: Returns True if all checks succeed
    """
    uptime_centiseconds = 3153600000  # 365 days in hundredeths of a second

    # Compare live data with NB data.
    print(f"BEGIN: {device}")

    try:
        assert live_data["serial_number"] == device.serial.strip()
    except AssertionError:
        error_message = f"ERROR: {device} - Serial numbers do not match."
        raise err.DataError(message=error_message, error_type="SerialNumberMismatch", device=device, extra_data=(device, live_data))

    try:
        assert live_data["system_name"] == device.name.strip()
    except AssertionError:
        error_message = f"ERROR: {device} - Hostnames do not match."
        raise err.DataError(message=error_message, error_type="HostnameMismatch", device=device, extra_data=(device, live_data))

    try:
        assert live_data["hardware_model"] == device.device_type.model.strip()
    except AssertionError:
        error_message = f"ERROR: {device} - Hardware models do not match."
        raise err.DataError(message=error_message, error_type="HardwareModelMismatch", device=device, extra_data=(device, live_data))

    try:
        assert live_data["sw_version"] == device.platform.name.strip()
    except AssertionError:
        error_message = f"ERROR: {device} - Software versions do not match."
        raise err.DataError(message=error_message, error_type="SoftwareVersionMismatch", device=device, extra_data=(device, live_data))

    try:
        assert live_data["sys_uptime"] < uptime_centiseconds  # Hundredths of a second
    except AssertionError:
        error_message = f"ERROR: {device} - Uptime is more than 1 year."
        raise err.DataError(message=error_message, error_type="LongUptime", device=device, extra_data=(device, live_data))

    print(f"COMPLETE: {device}")

if __name__ == "__main__":
    # Constants
    ENVIRONMENTS = {
        "prod": {"url": "https://prod-netbox.domain", "env_var": "prod_nb_token"},
        "dev": {"url": "https://netbox-dev.domain", "env_var": "dev_nb_token"},
    }

    load_dotenv()

    # Load and parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-env",
        choices=ENVIRONMENTS.keys(),
        help="Choose 'prod' or 'dev' environment",
        required=True,
    )
    args = parser.parse_args()
    running_env = args.env

    # Get environment configuration
    env_config = ENVIRONMENTS[running_env]
    url = env_config["url"]
    api_token = os.environ.get(env_config["env_var"])
    if api_token is None:
        raise ValueError(f"API token for {running_env} environment not found")

    main(url, api_token)
