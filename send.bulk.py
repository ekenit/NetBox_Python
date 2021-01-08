__author__ = "Elliot Ekman"
__version__ = '1.0.1'

from nornir import InitNornir
from nornir.plugins.tasks import networking
from nornir.plugins.functions.text import print_result
from nornir.plugins.tasks.files import write_file
from nornir.plugins.functions.text import print_result, print_title
from nornir.plugins.tasks.networking import netmiko_send_config, netmiko_send_command
from napalm import get_network_driver
import pynetbox
import requests
import urllib3
import json
import re
from getpass import getpass


# Getpass function




def nornir_set_creds(norn, username=None, password=None,):
    """Handler so credentials don't need stored in clear in inventory."""
    if not username:
        username = input("Enter username: ")
    if not password:
        password = getpass()



    for host_obj in norn.inventory.hosts.values():
        host_obj.username = username
        host_obj.password = password




# Disable https warnings
urllib3.disable_warnings()
# Add NetBox Inventory
print_title('Initializing Inventory. Please wait... \n')

nr = InitNornir(
    inventory={
        "plugin": "nornir.plugins.inventory.netbox.NBInventory",
        "options": {
            "nb_url": "NETBOXURL",
            "nb_token": "NETBOXTOKEN",
            "ssl_verify": False,

        },
    },
)
from nornir.core.inventory import ConnectionOptions





session = requests.Session()
session.verify = False
nb = pynetbox.api(
    'NETBOXURL',
    # private_key_file='/path/to/private-key.pem',
    token='NETBOXTOKEN'
)
nb.http_session = session

# Information to script user
print_title("Nornir Push command script")
print("This script lets you send commands to devices based on NetBox Platform, Roles and Sites\n ")
print("Please look at NetBox Structure if unsure and this tool is primarily intended for configuration and runs exclusive in enable mode use with CAUTION.\n")
print("There is another script called send.cmd.py, that sends only show commands outside of enable mode\n")

print("First you need to enter the filter parameters\n")
print("The underlying logic here is that you enter filters, then later on you will apply them.\nDont want to filter on role or Site ? just press Enter\n")
print("Enter Filters, [Platform -> Role -> Site] -> Enter Command: [ Command ] -> Apply Filter [P,PR,PRS] -> Summarization of entered information.\n ")
print("Then there will be a summary of targeted devices")
print("And finally there is a yes / no promt\n")

print("\n\n")

# Here is all the pynetbox calls defined.

all_deviceplatforms = nb.dcim.platforms.all()
all_deviceroles = nb.dcim.device_roles.all()
all_sites = nb.dcim.sites.all()

# Here the user enters the input to strings.

print_title("Choose Platform (Mandatory due to syntax differences")
print(all_deviceplatforms)
inputplatform = input("Enter Platform: ").lower()
print("")
print_title("Choose Role (Optional, will target many devices if not specified) \n")
print(all_deviceroles)
inputrole = input("Enter Role: ").lower()
print("")
print_title("Choose Site  (Optional, will target many devices if not specified)  ")
print(all_sites)
inputsite = input("Enter Site: ").lower()
print("")
#tells the user that the file contains the following.
f = open('CONFIG-TO-SEND', 'r')
file_contents = f.read()
print_title("CONFIG-TO-SEND File contains the following information.\n")
print (file_contents)
print("")




def baseconfig(push):
    # Send config textfile to targets push.run(task=netmiko_send_config, config_file= "config_textfile")
    push.run(task=netmiko_send_config, config_file= "CONFIG-TO-SEND")

targets = nr.filter(platform=inputplatform)

targets1 = nr.filter(platform=inputplatform, role=inputrole)

targets2 = nr.filter(platform=inputplatform, role=inputrole, site=inputsite)

# Printing the entered information for extra clarification

print_title(
    "You have now added filters, now it's time to apply them \n[P] Platform\n[PR] Platform,Role\n[PRS] Platform,Role,Site ")
applyfilter = input("Enter P,PR or PRS: ").lower()
print()
print_title("This is the information you have entered.\n")
print("Platform:     " + inputplatform)
print("Role:         " + inputrole)
print("Site:         " + inputsite)
print("P/PR/PRS:     " + applyfilter)
print("Command:      " + file_contents)
print("")
print_title("And these are the targeted devices")
print()

# printing targeted devices based on applying filter.

p = nr.filter(platform=inputplatform)
pr = nr.filter(platform=inputplatform, role=inputrole)
prs = nr.filter(platform=inputplatform, role=inputrole, site=inputsite)


def netboxinfo(task):
    print(f"{task.host.name}\n")


if applyfilter.lower() in ('p'):
    p1 = p.run(task=netboxinfo)


elif applyfilter.lower() in ('pr'):
    p2 = pr.run(task=netboxinfo)


elif applyfilter.lower() in ('prs'):
    p3 = prs.run(task=netboxinfo)

# Enter Credentials and calling Getpass function above.

print("")
print_title('Enter your credentials below... \n')
nornir_set_creds(nr)
secret = input("Enter Enable Secret: ")
nr.inventory.defaults.connection_options['netmiko'] = ConnectionOptions(extras={'secret':secret})

# Yes or no question, if no the application quits directly, if yes then proceeds.

def yes_or_no(question):
    answer = input(question + "(y/n): ").lower().strip()
    print("")
    while not (answer == "y" or answer == "yes" or \
               answer == "n" or answer == "no"):
        print("Input yes or no")
        answer = input(question + "(y/n):").lower().strip()
        print("")
    if answer[0] == "y":
        return True
    else:
        return False


if yes_or_no("<(^-^<) Continue?:  "):
    print_title("┏(･o･)┛♪ SENDING ♪┗ (･o･) ┓\n\n" + file_contents)
else:
    print(" (⌣́_⌣̀) See you next time! ")
    quit()

# Sending the actual command based on filter

if applyfilter.lower() in ('p'):
    results = targets.run(task=baseconfig)
    print_result(results)

elif applyfilter.lower() in ('pr'):
    results1 = targets1.run(task=baseconfig)
    print_result(results1)

elif applyfilter.lower() in ('prs'):
    results2 = targets2.run(task=baseconfig)
    print_result(results2)

print("Successfully sent configuration, now the script clears CONFIG-TO-TEXT file")
open("CONFIG-TO-SEND", "w").close()

## eekman
