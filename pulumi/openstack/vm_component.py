import pulumi
import pulumi_openstack as openstack

class OpenStackVmComponent(pulumi.ComponentResource):
    """
    Un composant Pulumi pour créer une instance Nova avec Floating IP et volume Cinder optionnel.
    """
    def __init__(self, name, args, opts=None):
        super().__init__('pkg:index:OpenStackVmComponent', name, args, opts)

        # 1. Instance Nova
        vm_name = args['vm_name']
        vm_role = args['vm_role']
        disk_size_gb = args['disk_size_gb']

        # Script d'initialisation pour le serveur web (personnalisé)
        vm_user_data = pulumi.Output.all(vm_name, vm_role).apply(lambda args: f"""#!/bin/bash
echo "Hello from OpenStack Nova - Orchestré par Pulumi (Composant)! Je suis {args[0]} ({args[1]})" > index.html
nohup busybox httpd -f -p 80 &
""")

        self.instance = openstack.compute.Instance(vm_name,
            name=vm_name,
            image_id=args['image_id'],
            flavor_name=args['flavor_name'],
            key_pair=args['key_pair_name'],
            security_groups=[args['security_group_name']],
            networks=[openstack.compute.InstanceNetworkArgs(
                uuid=args['network_id'],
            )],
            user_data=vm_user_data,
            opts=pulumi.ResourceOptions(parent=self))



        # 4. Volume Cinder (si rôle 'db')
        if vm_role == "db":
            db_volume = openstack.blockstorage.Volume(f"volume-{vm_name}",
                name=f"volume-{vm_name}",
                size=disk_size_gb, # Taille dynamique
                opts=pulumi.ResourceOptions(parent=self))

            # 5. Attachement du Volume à l'Instance
            openstack.compute.VolumeAttach(f"attach-{vm_name}",
                instance_id=self.instance.id,
                volume_id=db_volume.id,
                device="/dev/vdb",
                opts=pulumi.ResourceOptions(parent=self))
        
        self.instance_id = self.instance.id
        self.role = vm_role

        self.register_outputs({})
