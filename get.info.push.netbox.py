from nornir.plugins.tasks.networking import napalm_get
import pynetbox
import requests
from nornir import InitNornir
from pprint import pprint
import urllib3
from nornir.plugins.tasks.networking import netmiko_send_command
from nornir.core.inventory import ConnectionOptions
from nornir.plugins.functions.text import print_result




#Transform function from Nornir
def adapt_user_password(host):
    host.username = "USERNAME"
    host.password = "PASSWORD"

#Load config.yaml
nr = InitNornir(config_file="config.yaml")


nr.inventory.defaults.connection_options['netmiko'] = ConnectionOptions(extras={"optional_args": {"secret": "ENABLESECRET"}})
nr.inventory.defaults.connection_options['napalm'] = ConnectionOptions(extras={"optional_args": {"secret": "ENABLESECRET"}})

#Example sw10.domain.com
hosts = nr.filter(name="NETBOXFILTER")


urllib3.disable_warnings()

session = requests.Session()
session.verify = False
# load PynetBox
netbox = pynetbox.api('NETBOXURL', token='NETBOXTOKEN')
netbox.http_session = session

###########################################
##First get all interfaces for the host	 ##
###########################################
result = hosts.run(task=napalm_get, getters=["get_interfaces"])
for host in result:
    print("host is: ", host)
    print("result[{}][0] is: {}".format(host, result[host][0]))  ##Get id of host from netbox
    netboxHost = netbox.dcim.devices.get(name=str(host).upper())
    print("netbox host id is: ", netboxHost.id)  # key is interface name for each found interface for the host

    for interface in result[host][0].result['get_interfaces']:
        print("interface is : ", interface)
        pprint(interface)
        print("interface[0] is: ", interface[0])
        print("Data for host: {} interface: {} is".format(host, result[host][0].result['get_interfaces'][
            interface]))  ## Add netbox interface to host
        try:
            response = netbox.dcim.interfaces.create(
                device=netboxHost.id,
                name=interface,
                form_factor=1200,
                type="other",
                mac_address=result[host][0].result['get_interfaces'][interface]['mac_address'],
                enabled=result[host][0].result['get_interfaces'][interface]['is_enabled'],
                mtu=result[host][0].result['get_interfaces'][interface]['mtu'],
                description=result[host][0].result['get_interfaces'][interface]['description'],
            )
            print("response for creating interface: {} on host: {} is: ".format(interface, host))
        except Exception as e:
            print("Something went wrong with add interface to netbox")
            print("error is: ", e)

###################################################
##2 get all IPs for all interfaces on the host	##
###################################################
result = hosts.run(task=napalm_get, getters=["get_interfaces_ip"])  ##Get interfaces list from netbox
netboxIntList = netbox.dcim.interfaces.all()
print("netbox interfaces list is: ", netboxIntList)
IP_N_PREFIX = ""
# for every host in nornir result find every interface in netbox that belongs to that host
for host in result:
    print("host is: ", host.upper())
    print("result[{}][0] is: {}".format(host, result[host][
        0]))  ## check each netbox interface if it belongs to current nornir host
    for nbInterface in netboxIntList:
        # print("nbInterface is: ", nbInterface)
        # print("host interface id is: ", nbInterface.id)
        # print("host interface name is: ", nbInterface.name)
        # print("host interface belongs to: ", nbInterface.device.name)
        # print("host interface device data is:")
        # pprint(dict(nbInterface.device))	  ##if current nornir host has an netbox interface that belongs to same host
        if host.upper() == nbInterface.device.name:
            print("host from nornir matches interface in netbox that belong to same host")
            ##If nornir found a interface with IP then it will exist in the nornir result
            ## so we check if the found netbox interface that belonged to current host has a key in nornir result
            ## then that is a interface we need to add a IP to
            if nbInterface.name in result[host][0].result['get_interfaces_ip']:
                print("data in nornir result for host interface")
                pprint(dict(result[host][0].result['get_interfaces_ip'][nbInterface.name]))
                print("ost")
                print("Nornir host interface IP data is: ",
                      result[host][0].result['get_interfaces_ip'][nbInterface.name]['ipv4'])
                for key in result[host][0].result['get_interfaces_ip'][nbInterface.name]['ipv4']:
                    print("Nornir host interface IP is: ", key)
                    print("Nornir host interface IP prefix is: ",
                          result[host][0].result['get_interfaces_ip'][nbInterface.name]['ipv4'][key]['prefix_length'])
                    IP_N_PREFIX = str(key) + "/" + str(
                        result[host][0].result['get_interfaces_ip'][nbInterface.name]['ipv4'][key]['prefix_length'])
                    print("")
                    print("IP_N_PREFIX to send is: ", IP_N_PREFIX)
                    print("nbInterface.id to send is: ", nbInterface.id)
                    print("")

                    try:
                        response = netbox.ipam.ip_addresses.create(
                            address=IP_N_PREFIX,
                            status=1,
                            description="",
                            interface=nbInterface.id
                        )
                    # print("response for creating IP: {} on interface: {} on host: {} is: ".format(IP_N_PREFIX, nbInterface.name, host))
                    # print(response)
                    except Exception as e:
                        print("Something went wrong with add IP to interface for Host in netbox")
                        print("error is: ", e)


###########################
#  3 Change Device name to Hostname on Device, Also add serialnumber and license type.
###########################


result = hosts.run(netmiko_send_command, command_string="show version", use_genie=True)
for host in result:
    netboxHost = netbox.dcim.devices.get(name=str(host).upper())
    print("netbox host id is: ", netboxHost.id)  # key is interface name for each found interface for the host
    print("result[{}][0] is: {}".format(host, result[host][0]))
    lic = result[host][0].result['version']['license_level']
    lictype = result[host][0].result['version']['license_type']
    imgver = result[host][0].result['version']['system_image']
    licenses = "{" + "license_level: " + lic + ", " + "license_type: " +lictype + ", " + "system_image: " +imgver + "}"


    try:
        netboxhost_update_dict = dict(

            name=result[host][0].result['version']['hostname'],
            serial=result[host][0].result['version']['chassis_sn'],
            comments=licenses



        )

        # Ask Pynetbox to update object with attributes/values in rtr2_update_dict
        netboxHost.update(netboxhost_update_dict)

    except Exception as e:
            print("Something went wrong with device update.")
            print("error is: ", e)



####################################
### 4 Add platform items ####
####################################

#result = hosts.run(netmiko_send_command, command_string="show inventory", use_genie=True)
#for host in result:
#    print("host is: ", host)
#    print("result[{}][0] is: {}".format(host, result[host][0]))  ##Get id of host from netbox
#    netboxHost = netbox.dcim.devices.get(name=str(host).upper())
#    print("netbox host id is: ", netboxHost.id)  # key is interface name for each found interface for the host


#try:
#    response = netbox.dcim.inventory_items.create(
#        device=netboxHost.id,
#        name=result[host][0].result['slot']['0']['other']['C892FSP-K9']['name'],
#        part_id=result[host][0].result['slot']['0']['other']['C892FSP-K9']['pid'],
#        serial=result[host][0].result['slot']['0']['other']['C892FSP-K9']['sn'],
#        description=result[host][0].result['slot']['0']['other']['C892FSP-K9']['descr'],
#
#
#    )
#
#    # Ask Pynetbox to update object with attributes/values in rtr2_update_dict
#
#
#except Exception as e:
#    print("Something went wrong with add IP to interface for Host in netbox")
#    print("error is: ", e)


