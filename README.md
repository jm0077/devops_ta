# Microservicio DevOps

Este proyecto implementa un microservicio REST con un endpoint `/DevOps` utilizando Python y Flask, desplegado en Azure Kubernetes Service (AKS).

## Estructura del Proyecto

```
/
├── src/
│   └── app.py
├── tests/
│   └── test_app.py
├── manifests/
│   ├── deployment.yml
│   ├── service.yml
│   ├── ingress.yml
│   ├── redis-deployment.yml
│   └── redis-service.yml
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .gitignore
├── README.md
├── azure-pipelines.yml
├── main.tf
└── swagger.json
```

## Requisitos

- Python 3.9+
- Docker
- Azure CLI
- Terraform

## Configuración

1. Clonar el repositorio
2. Instalar dependencias: `pip install -r requirements.txt`
3. Configurar variables de entorno de Azure

## Despliegue

1. Inicializar Terraform: `terraform init`
2. Aplicar la infraestructura: `terraform apply`
3. Configurar Azure DevOps pipeline

## Pruebas

Ejecutar pruebas unitarias: `python -m unittest discover tests`

## CI/CD

El pipeline de CI/CD está configurado en `azure-pipelines.yml` y se ejecuta automáticamente en Azure DevOps.

## Contribuir

Por favor, lea CONTRIBUTING.md para detalles sobre nuestro código de conducta y el proceso para enviarnos pull requests.

## Licencia

Este proyecto está licenciado bajo la Licencia MIT - vea el archivo LICENSE.md para más detalles.