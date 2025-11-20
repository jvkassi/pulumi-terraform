import pulumi
import pulumi_aws as aws

class AwsVmComponent(pulumi.ComponentResource):
    """
    Un composant Pulumi pour créer une instance EC2 avec un volume EBS optionnel.
    """
    def __init__(self, name, args, opts=None):
        super().__init__('pkg:index:AwsVmComponent', name, args, opts)

        # 1. Instance EC2
        vm_name = args['vm_name']
        vm_role = args['vm_role']
        disk_size_gb = args['disk_size_gb']
        
        # Script d'initialisation pour le serveur web (personnalisé)
        vm_user_data = pulumi.Output.all(vm_name, vm_role).apply(lambda args: f"""#!/bin/bash
echo "Hello from AWS EC2 - Orchestré par Pulumi (Composant)! Je suis {args[0]} ({args[1]})" > index.html
nohup busybox httpd -f -p 80 &
""")

        self.instance = aws.ec2.Instance(vm_name,
            ami=args['ami_id'],
            instance_type=args['instance_type'],
            key_name=args['key_pair_name'],
            subnet_id=args['subnet_id'],
            vpc_security_group_ids=[args['security_group_id']],
            user_data=vm_user_data,
            tags={
                "Name": vm_name,
                "Role": vm_role,
            },
            root_block_device=aws.ec2.InstanceRootBlockDeviceArgs(
                volume_size=disk_size_gb, # Taille dynamique pour le disque racine
            ),
            opts=pulumi.ResourceOptions(parent=self))

        # 2. Volume EBS (si rôle 'db')
        if vm_role == "db":
            db_volume = aws.ebs.Volume(f"volume-{vm_name}",
                availability_zone=args['availability_zone'],
                size=disk_size_gb, # Taille dynamique pour le volume de données
                type="gp3",
                tags={
                    "Name": f"volume-{vm_name}",
                    "Role": vm_role,
                },
                opts=pulumi.ResourceOptions(parent=self))

            # 3. Attachement du Volume à l'Instance
            aws.ec2.VolumeAttachment(f"attach-{vm_name}",
                device_name="/dev/sdh",
                volume_id=db_volume.id,
                instance_id=self.instance.id,
                opts=pulumi.ResourceOptions(parent=self))
        
        self.public_ip = self.instance.public_ip
        self.instance_id = self.instance.id
        self.role = vm_role

        self.register_outputs({})
