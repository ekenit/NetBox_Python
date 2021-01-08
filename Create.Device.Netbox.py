import pynetbox
import requests
import urllib3

#Disable SSL warnings
urllib3.disable_warnings()

session = requests.Session()
session.verify = False
#load PynetBox
nb = pynetbox.api(
    'NETBOXURL',
    token='NETBOXTOKEN'
)
nb.http_session = session



#Define variables to print later on
all_devicetypes = nb.dcim.device_types.all()
all_deviceroles = nb.dcim.device_roles.all()
all_sites = nb.dcim.sites.all()
all_platforms = nb.dcim.platforms.all()

#Ask the user for information regarding the devices.

print("This script pushes information to Netbox")
input_device_name = input ("Enter Device name: ")
print()
print(all_devicetypes)
input_device_type = input ("Enter Device Type: ").lower()
print()
print(all_deviceroles)
input_device_role = input ("Enter Device role: ").lower()
print ()
print(all_sites)
input_device_site = input ("Enter Device Site: ").lower()
print()
input_ip_addr = input ("Enter Device IP with mask: ")
print()
print(all_platforms)
inputplatform = input ("Enter platform: ")
serial = input ("Enter serial: ")
comments = input ("Enter extra information: ")

# Retrieve objects needed for creation of the device
dev_type = nb.dcim.device_types.get(slug=input_device_type)
dev_role = nb.dcim.device_roles.get(slug=input_device_role)
dev_site = nb.dcim.sites.get(slug=input_device_site)

# Prepare dict with attributes for our device
dev_dict = dict(
    name=input_device_name,
    device_type=dev_type.id,
    device_role=dev_role.id,
    site=dev_site.id,
    serial=serial,
    comments=comments,
)

# Add device to NetBox and store resulting object in "new_dev"
new_dev = nb.dcim.devices.create(dev_dict)

# Prepare dict with attributes for Management interface
intf_dict = dict(
    name=input_device_name,
    form_factor=0,
    description="Mgmt",
    device=new_dev.id,
    type="virtual",
)

# Add interface to NetBox and store resulting object in "new_intf"
new_intf = nb.dcim.interfaces.create(intf_dict)

#Get id from new interface and store it.
new_interface = nb.dcim.interfaces.get(name=input_device_name)

# Prepare dict with attributes for Management IP address
ip_add_dict = dict(
    address=input_ip_addr,
    status=1,
    description="Management IP for {}".format(dev_dict["name"]),
    interface=new_interface.id,
    )

# Add interface to NetBox and store resulting object in "new_ip"

new_ip = nb.ipam.ip_addresses.create(ip_add_dict)

#set interface as primary

primary_name = nb.dcim.devices.get(name=input_device_name)
primary_network = nb.ipam.ip_addresses.get(address=input_ip_addr)
primary_platform= nb.dcim.platforms.get(name=inputplatform)
primary_update_dict = dict(
    device=primary_name.id,
    primary_ip=primary_network.id,
    primary_ip4=primary_network.id,
    platform=primary_platform.id,
)

#  PynetBox to update our object
primary_name.update(primary_update_dict)


# Display summary
print(
    "Device '{dev}' created with interface '{intf}', which has IP {ipadd}.".format(
        dev=dev_dict["name"], intf=intf_dict["name"], ipadd=ip_add_dict["address"]
    )
)
