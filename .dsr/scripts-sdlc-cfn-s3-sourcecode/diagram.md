```mermaid
flowchart TD
    User[User/Deployer]
    S3[(S3 Bucket<br>idp-sdlc-sourcecode)]
    
    User -->|Upload Deployment Artifacts| S3
    User -->|Access Versioned Objects| S3
    
    classDef storage fill:#3b78cf,stroke:#333,stroke-width:2px;
    classDef user fill:#f96,stroke:#333,stroke-width:2px;
    
    class S3 storage;
    class User user;
```