```python
import pulumi
from pulumi_azure_native import network, resources
import ipaddress

class VdcNetwork(pulumi.ComponentResource):
    def __init__(self, name, resource_group_name, address_space, opts=None):
        super().__init__('custom:network:VdcNetwork', name, {}, opts)

        # Validate and parse the address space
        try:
            network_address_space = ipaddress.ip_network(address_space)
        except ValueError as e:
            raise ValueError(f"Invalid address space: {e}")

        # Create a virtual network
        self.vnet = network.VirtualNetwork(
            f"{name}-vnet",
            resource_group_name=resource_group_name,
            address_space=network.AddressSpace(
                address_prefixes=[str(network_address_space)]
            ),
            opts=pulumi.ResourceOptions(parent=self)
        )

        # Create subnets for DMZ, Gateway, and Bastion
        self.dmz_subnet = network.Subnet(
            f"{name}-dmz-subnet",
            resource_group_name=resource_group_name,
            virtual_network_name=self.vnet.name,
            address_prefix="10.0.1.0/24",
            opts=pulumi.ResourceOptions(parent=self.vnet)
        )

        self.gateway_subnet = network.Subnet(
            f"{name}-gateway-subnet",
            resource_group_name=resource_group_name,
            virtual_network_name=self.vnet.name,
            address_prefix="10.0.2.0/24",
            opts=pulumi.ResourceOptions(parent=self.vnet)
        )

        self.bastion_subnet = network.Subnet(
            f"{name}-bastion-subnet",
            resource_group_name=resource_group_name,
            virtual_network_name=self.vnet.name,
            address_prefix="10.0.3.0/24",
            opts=pulumi.ResourceOptions(parent=self.vnet)
        )

        # Create Azure Firewall
        self.firewall = network.AzureFirewall(
            f"{name}-firewall",
            resource_group_name=resource_group_name,
            virtual_network_name=self.vnet.name,
            ip_configurations=[network.AzureFirewallIPConfigurationArgs(
                name="firewall-ipconfig",
                subnet=self.dmz_subnet.id
            )],
            opts=pulumi.ResourceOptions(parent=self.vnet)
        )

        # Create Azure Bastion
        self.bastion = network.BastionHost(
            f"{name}-bastion",
            resource_group_name=resource_group_name,
            virtual_network_name=self.vnet.name,
            ip_configurations=[network.BastionHostIPConfigurationArgs(
                name="bastion-ipconfig",
                subnet=self.bastion_subnet.id
            )],
            opts=pulumi.ResourceOptions(parent=self.vnet)
        )

        # Register outputs
        self.register_outputs({
            'vnet': self.vnet,
            'dmz_subnet': self.dmz_subnet,
            'gateway_subnet': self.gateway_subnet,
            'bastion_subnet': self.bastion_subnet,
            'firewall': self.firewall,
            'bastion': self.bastion
        })

# Example usage
def create_vdc_network():
    resource_group = resources.ResourceGroup("vdc-rg")
    vdc_network = VdcNetwork(
        name="vdc",
        resource_group_name=resource_group.name,
        address_space="10.0.0.0/16"
    )

pulumi.export("vdc_network", create_vdc_network())
```