```mermaid
flowchart TD
    CustomResource[Custom Resource]
    BDAProjectLambda((BDA Project Lambda))
    BedrockService[Bedrock Service]
    
    CustomResource -->|Custom::BDAProject Request| BDAProjectLambda
    BDAProjectLambda -->|CreateDataAutomationProject| BedrockService
    BDAProjectLambda -->|AddBlueprintToProject| BedrockService
    BedrockService -->|Project & Blueprint Data| BDAProjectLambda
    BDAProjectLambda -->|Response| CustomResource
```