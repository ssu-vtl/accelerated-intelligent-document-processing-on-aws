# Threat ID Glossary & Cross-Reference Guide

**📖 Navigation:** [🏠 Main README](README.md) | [📋 Executive Summary](deliverables/executive-summary.md) | [🏗️ Architecture](architecture/system-overview.md) | [⚖️ Risk Assessment](risk-assessment/risk-matrix.md)

---

## Overview
This glossary explains the threat identification (ID) naming convention used throughout the GenAI IDP Accelerator threat model and provides cross-references to detailed threat analysis.

## Threat ID Naming Convention

### Format: `[CATEGORY].[ID]` or `[CATEGORY]-[COMPONENT]-[TYPE]`

## Threat Categories Explained

### **AME** - AI/ML Model Exploitation
**Definition**: Threats targeting AI/ML models, prompts, and model behavior
**Examples**:
- **AME.1**: Coordinated Multi-Model Prompt Injection Attack → [📖 Details](threat-analysis/threat-designer-results/ai-generated-threats.md#ame1-coordinated-multi-model-prompt-injection-attack)
- **AME.2**: Foundation Model Backdoor Exploitation → [📖 Details](threat-analysis/threat-designer-results/ai-generated-threats.md#ame2-foundation-model-backdoor-exploitation)

### **SAC** - Serverless Architecture Complexity  
**Definition**: Threats exploiting complex serverless component interactions
**Examples**:
- **SAC.1**: Distributed State Manipulation Attack → [📖 Details](threat-analysis/threat-designer-results/ai-generated-threats.md#sac1-distributed-state-manipulation-attack)
- **SAC.2**: Cross-Function Privilege Escalation Chain → [📖 Details](threat-analysis/threat-designer-results/ai-generated-threats.md#sac2-cross-function-privilege-escalation-chain)

### **DAP** - Document-Borne Advanced Persistent
**Definition**: Threats using malicious documents for persistent attacks
**Examples**:
- **DAP.1**: Polyglot Document Persistence Attack → [📖 Details](threat-analysis/threat-designer-results/ai-generated-threats.md#dap1-polyglot-document-persistence-attack)

### **EWR** - Economic Warfare and Resource Exhaustion
**Definition**: Threats designed to cause financial damage through resource abuse
**Examples**:
- **EWR.1**: AI Model Token Economics Attack → [📖 Details](threat-analysis/threat-designer-results/ai-generated-threats.md#ewr1-ai-model-token-economics-attack)

### **CPA** - Cross-Pattern Attack
**Definition**: Threats exploiting multiple processing patterns simultaneously
**Examples**:
- **CPA.1**: Pattern Migration Attack → [📖 Details](threat-analysis/threat-designer-results/ai-generated-threats.md#cpa1-pattern-switching-exploitation-attack)

## Pattern-Specific Threat IDs

### **P1.T##** - Pattern 1 (Bedrock Data Automation) Threats
**Examples**:
- **P1.T01**: BDA Service Configuration Poisoning → [📖 Details](threat-analysis/pattern-specific-threats.md#p1t01-bda-service-configuration-poisoning)
- **P1.T02**: BDA Model Response Injection → [📖 Details](threat-analysis/pattern-specific-threats.md#p1t02-bda-model-response-injection)
- **P1.T03**: BDA Quota Exhaustion Attack → [📖 Details](threat-analysis/pattern-specific-threats.md#p1t03-bda-quota-exhaustion-attack)

### **P2.T##** - Pattern 2 (Textract + Bedrock) Threats
**Examples**:
- **P2.T01**: Multi-Stage Prompt Injection Chain → [📖 Details](threat-analysis/pattern-specific-threats.md#p2t01-multi-stage-prompt-injection-chain)
- **P2.T02**: Few-Shot Example Poisoning → [📖 Details](threat-analysis/pattern-specific-threats.md#p2t02-few-shot-example-poisoning)
- **P2.T03**: Inter-Stage Data Tampering → [📖 Details](threat-analysis/pattern-specific-threats.md#p2t03-inter-stage-data-tampering)

### **P3.T##** - Pattern 3 (Textract + SageMaker + Bedrock) Threats
**Examples**:
- **P3.T01**: SageMaker Endpoint Model Substitution → [📖 Details](threat-analysis/pattern-specific-threats.md#p3t01-sagemaker-endpoint-model-substitution)
- **P3.T02**: UDOP Adversarial Input Attack → [📖 Details](threat-analysis/pattern-specific-threats.md#p3t02-udop-adversarial-input-attack)
- **P3.T03**: Cross-Service Privilege Escalation Chain → [📖 Details](threat-analysis/pattern-specific-threats.md#p3t03-cross-service-privilege-escalation-chain)

## STRIDE-Based Threat IDs

### Format: `STRIDE-[COMPONENT]-[THREAT_TYPE]`

#### **STRIDE Components**:
- **S3** = Amazon S3 Buckets
- **LAMBDA** = AWS Lambda Functions
- **COG** = Amazon Cognito
- **AS** = AWS AppSync
- **BR** = Amazon Bedrock
- **SM** = Amazon SageMaker
- **CF** = Amazon CloudFront
- **SFN** = AWS Step Functions
- **SQS** = Amazon SQS
- **DDB** = Amazon DynamoDB
- **TX** = Amazon Textract
- **WAF** = AWS WAF

#### **STRIDE Threat Types**:
- **S** = Spoofing
- **T** = Tampering  
- **R** = Repudiation
- **I** = Information Disclosure
- **D** = Denial of Service
- **E** = Elevation of Privilege

### **Examples**:
- **STRIDE-S3-I**: S3 Bucket Information Disclosure → [📖 Details](threat-analysis/stride-analysis.md#s3-input-bucket)
- **STRIDE-LAMBDA-E**: Lambda Privilege Escalation → [📖 Details](threat-analysis/stride-analysis.md#aws-lambda-functions)
- **STRIDE-BR-T**: Bedrock Prompt Injection (Tampering) → [📖 Details](threat-analysis/stride-analysis.md#amazon-bedrock-models)
- **STRIDE-COG-T**: Cognito Token Manipulation → [📖 Details](threat-analysis/stride-analysis.md#amazon-cognito-user-pool)
- **STRIDE-AS-T**: AppSync Query Injection → [📖 Details](threat-analysis/stride-analysis.md#appsync-graphql-api)

## Data Flow Threat IDs

### **DF.##** - Data Flow Threats
**Definition**: Threats targeting data movement and transformation processes
**Examples**:
- **DF.1**: Data in Transit Interception → [📖 Details](architecture/data-flows.md#df1-data-in-transit-interception)
- **DF.2**: Cross-Service Data Leakage → [📖 Details](architecture/data-flows.md#df2-cross-service-data-leakage)
- **DF.5**: Event Stream Manipulation → [📖 Details](architecture/data-flows.md#df5-event-stream-manipulation)
- **DF.6**: Logging Information Disclosure → [📖 Details](architecture/data-flows.md#df6-logging-information-disclosure)

## Cross-Pattern Threat IDs

### **CPT.T##** - Cross-Pattern Threats
**Definition**: Threats that exploit interactions between multiple processing patterns
**Examples**:
- **CPT.T01**: Pattern Migration Attack → [📖 Details](threat-analysis/pattern-specific-threats.md#cptt01-pattern-migration-attack)

## Risk Priority Levels

### **P0 - Critical Priority** (8 threats)
Immediate action required, business-critical impact

### **P1 - High Priority** (8 threats)  
Urgent action, significant business impact

### **P2 - Medium Priority** (8 threats)
Planned action, moderate business impact

### **P3 - Low Priority** (7 threats)
Long-term action, limited business impact

## Quick Reference: Threat ID to Document Mapping

| Threat Category | Count | Primary Document | Risk Level Range |
|----------------|-------|------------------|------------------|
| **AI/ML Exploitation (AME)** | 2 | [🤖 AI-Generated Threats](threat-analysis/threat-designer-results/ai-generated-threats.md) | P0-P1 |
| **Serverless Complexity (SAC)** | 2 | [🤖 AI-Generated Threats](threat-analysis/threat-designer-results/ai-generated-threats.md) | P0-P1 |
| **Document-Borne (DAP)** | 1 | [🤖 AI-Generated Threats](threat-analysis/threat-designer-results/ai-generated-threats.md) | P1 |
| **Economic Warfare (EWR)** | 1 | [🤖 AI-Generated Threats](threat-analysis/threat-designer-results/ai-generated-threats.md) | P2 |
| **Cross-Pattern (CPA, CPT)** | 2 | [🔍 Pattern-Specific Threats](threat-analysis/pattern-specific-threats.md) | P1 |
| **Pattern 1 (P1.T##)** | 3 | [🔍 Pattern-Specific Threats](threat-analysis/pattern-specific-threats.md) | P0-P2 |
| **Pattern 2 (P2.T##)** | 3 | [🔍 Pattern-Specific Threats](threat-analysis/pattern-specific-threats.md) | P0-P2 |
| **Pattern 3 (P3.T##)** | 3 | [🔍 Pattern-Specific Threats](threat-analysis/pattern-specific-threats.md) | P0-P1 |
| **STRIDE Components** | 14 | [🎯 STRIDE Analysis](threat-analysis/stride-analysis.md) | P0-P3 |
| **Data Flow (DF.##)** | 4 | [🌊 Data Flows](architecture/data-flows.md) | P2-P3 |

## Finding Detailed Threat Information

### **For Any Threat ID:**
1. **Check Risk Assessment**: [⚖️ Risk Matrix](risk-assessment/risk-matrix.md) - Shows priority and risk score
2. **Find Category Document**: Use the table above to find the primary document
3. **Search Document**: Use browser search (Ctrl+F) for the specific threat ID
4. **Cross-References**: Follow the hyperlinks in each document for related threats

### **For Implementation Guidance:**
- **All Threats**: [🛠️ Implementation Guide](deliverables/implementation-guide.md) - Technical mitigation steps
- **Executive View**: [📋 Executive Summary](deliverables/executive-summary.md) - Business-focused overview

This glossary ensures all threat IDs are clearly defined and easily accessible throughout the threat model documentation.
