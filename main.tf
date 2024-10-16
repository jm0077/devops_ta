# Configuración del proveedor de Azure
terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.75.0"
    }
  }
}

provider "azurerm" {
  features {}
  skip_provider_registration = true
}

# Grupo de recursos
resource "azurerm_resource_group" "rg" {
  name     = "rg-devops-ta"
  location = "East US"
}

# AKS Cluster
resource "azurerm_kubernetes_cluster" "aks" {
  name                = "aks-devops-ta"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  dns_prefix          = "aks-devops-ta"

  default_node_pool {
    name       = "default"
    node_count = 1
    vm_size    = "Standard_D2pds_v5"
  }

  identity {
    type = "SystemAssigned"
  }
}

# Node Pool con auto-escalado
resource "azurerm_kubernetes_cluster_node_pool" "autoscale" {
  name                  = "autoscale"
  kubernetes_cluster_id = azurerm_kubernetes_cluster.aks.id
  vm_size               = "Standard_D2pds_v5"
  node_count            = 1
  min_count             = 1
  max_count             = 3
  enable_auto_scaling   = true
}

# API Management
resource "azurerm_api_management" "apim" {
  name                = "apim-devops-ta"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  publisher_name      = "DevOps TA"
  publisher_email     = "devops@example.com"
  sku_name            = "Developer_1"
}

# API en API Management
resource "azurerm_api_management_api" "api" {
  name                = "example-api"
  resource_group_name = azurerm_resource_group.rg.name
  api_management_name = azurerm_api_management.apim.name
  revision            = "1"
  display_name        = "Example API"
  path                = "example"
  protocols           = ["https"]

  import {
    content_format = "openapi+json"
    content_value  = file("${path.module}/swagger.json")
  }
}

resource "azurerm_api_management_api_policy" "api_policy" {
  api_name            = azurerm_api_management_api.api.name
  api_management_name = azurerm_api_management.apim.name
  resource_group_name = azurerm_resource_group.rg.name

  xml_content = <<XML
<policies>
  <inbound>
    <base />
    <set-header name="X-Parse-REST-API-Key" exists-action="override">
      <value>2f5ae96c-b558-4c7b-a590-a501ae1c3f6c</value>
    </set-header>
  </inbound>
</policies>
XML
}

resource "azurerm_container_registry" "acr" {
  name                = "acrdevopsta"
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location
  sku                 = "Basic"
  admin_enabled       = true
}

output "acr_login_server" {
  value = azurerm_container_registry.acr.login_server
}

output "acr_admin_username" {
  value = azurerm_container_registry.acr.admin_username
}

output "acr_admin_password" {
  value     = azurerm_container_registry.acr.admin_password
  sensitive = true
}

output "kube_config" {
  value     = azurerm_kubernetes_cluster.aks.kube_config_raw
  sensitive = true
}