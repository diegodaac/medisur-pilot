# Comandos de Azure (documentados, NO ejecutados)

> Regla del proyecto: estos comandos crean o modifican recursos de Azure. Claude Code
> los muestra y espera confirmación de Diego antes de ejecutar cualquiera.
> Los valores entre `<...>` se reemplazan a mano. No se escribe ninguna contraseña aquí:
> las VMs usan llave SSH.

## 0. Variables

```bash
az login
az account show --query "{suscripcion:name, id:id}" -o table

RG="<grupo-de-recursos-de-LAB-03>"          # donde ya vive VM-K8S
LOC="<mexicocentral|canadacentral|westus2|westus|chilecentral>"   # la MISMA región que VM-K8S
VM_K8S="<nombre-vm-lab03>"
MI_IP="$(curl -s https://api.ipify.org)/32"  # IP pública de Diego para las reglas del NSG
```

## 1. Verificar VM-K8S (solo lectura)

```bash
az vm show -g "$RG" -n "$VM_K8S" --query "{tamano:hardwareProfile.vmSize, region:location, so:storageProfile.imageReference.sku}" -o table
az vm list-ip-addresses -g "$RG" -n "$VM_K8S" -o table
az network vnet list -g "$RG" --query "[].{vnet:name, subnets:subnets[].name}" -o json
# Dentro de la VM:  microk8s status --wait-ready   (debe estar funcionando; Ubuntu 22.04, B2ms)
```

## 2. Crear VM-TOOLS (misma región y MISMA VNet que VM-K8S)

```bash
VNET="<vnet-de-vm-k8s>"
SUBNET="<subnet-de-vm-k8s>"

az vm create \
  -g "$RG" -n vm-tools -l "$LOC" \
  --image Canonical:0001-com-ubuntu-server-jammy:22_04-lts-gen2:latest \
  --size Standard_B4ms \
  --os-disk-size-gb 64 --storage-sku StandardSSD_LRS \
  --vnet-name "$VNET" --subnet "$SUBNET" \
  --admin-username azureuser --generate-ssh-keys \
  --public-ip-sku Standard
```

## 3. NSG de VM-TOOLS (22 / 8080 / 9000 / 3000 / 9090)

```bash
NSG_TOOLS="vm-toolsNSG"   # nombre que crea `az vm create`; verificar con `az network nsg list -g $RG -o table`

# Rangos de GitHub (hooks) para el webhook de Jenkins:
curl -s https://api.github.com/meta | jq -r '.hooks[]' | tr '\n' ' '   # copiar el resultado a HOOKS

az network nsg rule create -g "$RG" --nsg-name "$NSG_TOOLS" -n ssh-diego      --priority 100 --access Allow --protocol Tcp --direction Inbound --source-address-prefixes "$MI_IP" --destination-port-ranges 22
az network nsg rule create -g "$RG" --nsg-name "$NSG_TOOLS" -n jenkins-diego  --priority 110 --access Allow --protocol Tcp --direction Inbound --source-address-prefixes "$MI_IP" --destination-port-ranges 8080
az network nsg rule create -g "$RG" --nsg-name "$NSG_TOOLS" -n jenkins-hooks  --priority 120 --access Allow --protocol Tcp --direction Inbound --source-address-prefixes $HOOKS --destination-port-ranges 8080
az network nsg rule create -g "$RG" --nsg-name "$NSG_TOOLS" -n sonar-grafana-prom-diego --priority 130 --access Allow --protocol Tcp --direction Inbound --source-address-prefixes "$MI_IP" --destination-port-ranges 9000 3000 9090
```

## 4. NSG de VM-K8S

```bash
NSG_K8S="<nsg-de-vm-k8s>"
IP_PRIV_TOOLS="$(az vm list-ip-addresses -g "$RG" -n vm-tools --query '[0].virtualMachine.network.privateIpAddresses[0]' -o tsv)"

az network nsg rule create -g "$RG" --nsg-name "$NSG_K8S" -n ssh-k8s-diego   --priority 100 --access Allow --protocol Tcp --direction Inbound --source-address-prefixes "$MI_IP" --destination-port-ranges 22 16443
# NodePort 30080 (la app) abierto a Diego para `curl /version`; desde VM-TOOLS ya entra por la VNet.
az network nsg rule create -g "$RG" --nsg-name "$NSG_K8S" -n app-diego       --priority 110 --access Allow --protocol Tcp --direction Inbound --source-address-prefixes "$MI_IP" --destination-port-ranges 30080
# Exporters: SOLO desde la IP privada de VM-TOOLS (9100 node_exporter, 30808 kube-state-metrics).
az network nsg rule create -g "$RG" --nsg-name "$NSG_K8S" -n exporters-tools --priority 120 --access Allow --protocol Tcp --direction Inbound --source-address-prefixes "$IP_PRIV_TOOLS" --destination-port-ranges 9100 30808
```

## 5. Costos (obligatorios)

```bash
# Apagado automático diario en ambas VMs (hora UTC, formato HHMM)
az vm auto-shutdown -g "$RG" -n vm-tools     --time 0600
az vm auto-shutdown -g "$RG" -n "$VM_K8S"    --time 0600

# Presupuesto de 50 USD con alerta (también se puede crear en el portal: Cost Management > Budgets)
az consumption budget create --budget-name medisur-50usd --amount 50 --category cost \
  --time-grain monthly --start-date "$(date +%Y-%m-01)" --end-date "<AAAA-MM-DD>" \
  --resource-group "$RG"
# Agregar a mano en el portal las notificaciones por correo al 80 % y 100 %.

# Detener SIEMPRE con deallocate (no desde dentro de la VM):
az vm deallocate -g "$RG" -n vm-tools
az vm deallocate -g "$RG" -n "$VM_K8S"
```

## 6. Al terminar el curso

```bash
az group delete -n "$RG" --yes --no-wait     # borra TODO el grupo; confirmar antes
```
