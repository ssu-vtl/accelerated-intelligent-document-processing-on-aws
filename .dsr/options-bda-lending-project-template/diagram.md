```mermaid
flowchart TD
    User[User/Admin]
    CFN[CloudFormation]
    CustomResource[Custom Resource]
    BDAProjectLambda[BDA Project Lambda]
    BedrockService[Bedrock Service]
    
    User -->|Deploy Template| CFN
    CFN -->|Create/Update| BDAProjectLambda
    CFN -->|Invoke| CustomResource
    CustomResource -->|ServiceToken| BDAProjectLambda
    BDAProjectLambda -->|Create/Manage Project| BedrockService
    BDAProjectLambda -->|Add Blueprints| BedrockService
    BedrockService -->|Project ARN| BDAProjectLambda
    BedrockService -->|Blueprint ARNs| BDAProjectLambda
    BDAProjectLambda -->|Project/Blueprint Data| CustomResource
    CustomResource -->|Output ARNs| CFN
    CFN -->|Project/Blueprint ARNs| User
```