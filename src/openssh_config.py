# Standard Library
import argparse
from jinja2 import Environment, FileSystemLoader
import os
import sys

# Non-Standard Library
from dotenv import load_dotenv
import pynetbox

# Custom imports
import error_handling.custom_errors as err
import error_handling.error_reporting as err_report


def main(ssh_user: str, api_token: str, url: str):
    """Main orchestrator function to be ran by CI/CD.

    Args:
        ssh_user (str): Username of the admin, typically .a account. Collected when running from CI/CD.
        api_token (str): String representation of the service account's API token.
        url (str): Full URL for the proper Netbox environment's API base endpoint.
    """

    try:
        devices = collect_nb_devices(url=url, api_token=api_token)
        ssh_conf = render_ssh_conf(devices=devices, ssh_user=ssh_user)
        write_to_file(ssh_conf)

    except err.DataError as e:
        err_report.log_parser(e)
        sys.exit(1)
    except Exception as e:
        raise (e)


def collect_nb_devices(url: str, api_token: str) -> set:
    """Collects relevant Netbox devices' hostnames and returns them as a list.

    Args:
        url (str): URL of the Netbox instance you want to collect from.
        api_token (str): API token used for connecting to the provided URL.

    Raises:
        err.DataError: Custom data error for logging purposes in conjunction with error_handling.error_reporting.py

    Returns:
        set: Set of collected devices' hostnames.
    """

    NB_ROLE_SEARCHLIST = ["production-switches", "production-routers"]

    try:
        # Initialize NetBox API
        nb = pynetbox.api(url=url, token=api_token)

        # Fetch devices
        nb_devices = nb.dcim.devices.filter(status="active", role=NB_ROLE_SEARCHLIST)

        # Output set
        devices = set()

        for nb_device in nb_devices:
            try:
                if nb_device.virtual_chassis:
                    vc_master = nb_device.virtual_chassis.master.name
                    dvc_lookup = nb.dcim.devices.get(name=vc_master)
                    dns_name = dvc_lookup.primary_ip4.dns_name
                    nb_device.dns_name = dns_name
                else:
                    nb_device.dns_name = nb_device.primary_ip4.dns_name

                if nb_device.dns_name == "":
                    nb_device.dns_name = "FIX_ME_IN_NETBOX"

            except AttributeError as e:
                nb_device.dns_name = "FIX_ME_IN_NETBOX"

            devices.add(nb_device)

        return devices

    except pynetbox.core.query.ContentError as e:
        error_message = (
            "ERROR: Incorrect Netbox URL passed to collect_nb_devices function."
        )
        raise err.DataError(message=error_message, extra_data={"original_exception": e})

    except pynetbox.core.query.RequestError as e:
        error_message = "ERROR: Netbox Request error."
        raise err.DataError(message=error_message, extra_data={"original_exception": e})

    except AttributeError as e:
        error_message = (
            f"ERROR: Could not find expected data in Netbox. Update Netbox data."
        )

        raise err.DataError(
            message=error_message,
            error_type="NetboxCompliancy",
            device=nb_device,
            extra_data={"original_exception": e},
        )

    except Exception as e:
        # Catch any unexpected exceptions and raise them with proper context
        error_message = f"ERROR: An unexpected error occurred: {str(e)}"
        raise err.DataError(message=error_message, extra_data={"original_exception": e})


def render_ssh_conf(devices: set, ssh_user: str):
    # Create a Jinja2 environment with the FileSystemLoader
    templateLoader = FileSystemLoader(searchpath="./src/templates/")
    env = Environment(loader=templateLoader)

    # Load the template from the specified directory
    template = env.get_template("ssh_conf.j2")

    # Render the template with the provided data
    ssh_conf = template.render(devices=devices, ssh_user=ssh_user)

    return ssh_conf


def write_to_file(ssh_conf):
    with open("artifacts/config", "w+") as f:
        f.write(ssh_conf)


if __name__ == "__main__":
    load_dotenv()

    # Load and parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-ssh_user",
        help="Provide your SSH username, usually your .a account.",
        required=True,
    )
    parser.add_argument(
        "-url",
        help="Netbox URL",
        required=True,
    )

    # # Parse args
    args = parser.parse_args()
    ssh_user = args.ssh_user
    url = args.url

    # # Get environment configuration
    api_token = os.environ.get("NB_API_TOKEN")

    # Pass collected data to main func
    main(ssh_user=ssh_user, api_token=api_token, url=url)
