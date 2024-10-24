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
  publisher_email     = "dms.staging01@outlook.com"
  sku_name            = "Developer_1"

  protocols {
    enable_http2 = true
  }

  security {
    enable_backend_ssl30  = false
    enable_backend_tls10  = false
    enable_backend_tls11  = false
    enable_frontend_ssl30 = false
    enable_frontend_tls10 = false
    enable_frontend_tls11 = false
  }
}

# Backend para la API
resource "azurerm_api_management_backend" "backend" {
  name                = "kubernetes-backend"
  resource_group_name = azurerm_resource_group.rg.name
  api_management_name = azurerm_api_management.apim.name
  protocol           = "http"
  url                = "http://devops-ta.duckdns.org" # Tu dominio actual
  
  tls {
    validate_certificate_chain = false
    validate_certificate_name  = false
  }
}

# API
resource "azurerm_api_management_api" "api" {
  name                = "devops-api"
  resource_group_name = azurerm_resource_group.rg.name
  api_management_name = azurerm_api_management.apim.name
  revision            = "1"
  display_name        = "DevOps API"
  path                = "api"
  protocols           = ["https"]
  service_url         = "http://devops-ta.duckdns.org"
  
  subscription_required = false
}

# Operación POST /DevOps
resource "azurerm_api_management_api_operation" "devops_post" {
  operation_id        = "post-devops"
  api_name           = azurerm_api_management_api.api.name
  api_management_name = azurerm_api_management.apim.name
  resource_group_name = azurerm_resource_group.rg.name
  display_name       = "DevOps Message"
  method             = "POST"
  url_template       = "/DevOps"
  description        = "Send a DevOps message"

  request {
    representation {
      content_type = "application/json"
      example {
        name  = "default"
        value = jsonencode({
          message       = "This is a test"
          to           = "Juan Perez"
          from         = "Rita Asturia"
          timeToLifeSec = 45
        })
      }
    }
  }

  response {
    status_code = 200
    representation {
      content_type = "application/json"
      example {
        name  = "default"
        value = jsonencode({
          message = "Hello Juan Perez your message will be send"
        })
      }
    }
  }
}

# Política global de la API
resource "azurerm_api_management_api_policy" "api_policy" {
  api_name            = azurerm_api_management_api.api.name
  api_management_name = azurerm_api_management.apim.name
  resource_group_name = azurerm_resource_group.rg.name

  xml_content = <<XML
<policies>
  <inbound>
    <base />
    <check-header name="X-Parse-REST-API-Key" failed-check-httpcode="401" failed-check-error-message="Invalid API Key" ignore-case="false">
      <value>2f5ae96c-b558-4c7b-a590-a501ae1c3f6c</value>
    </check-header>
    <check-header name="X-JWT-KWY" failed-check-httpcode="401" failed-check-error-message="Missing JWT token" ignore-case="false" />
    <validate-jwt header-name="X-JWT-KWY" failed-validation-httpcode="401" failed-validation-error-message="Invalid JWT token">
      <openid-config url="null" />
      <required-claims>
        <claim name="timeToLifeSec" match="any" />
      </required-claims>
      <signing-keys>
        <key>${var.jwt_secret}</key>
      </signing-keys>
    </validate-jwt>
    <set-backend-service backend-id="${azurerm_api_management_backend.backend.name}" />
  </inbound>
  <backend>
    <base />
  </backend>
  <outbound>
    <base />
  </outbound>
  <on-error>
    <base />
  </on-error>
</policies>
XML
}

# Variables necesarias
variable "jwt_secret" {
  description = "JWT secret key"
  type        = string
  sensitive   = true
}

# Outputs adicionales
output "apim_gateway_url" {
  value = "https://${azurerm_api_management.apim.gateway_url}"
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