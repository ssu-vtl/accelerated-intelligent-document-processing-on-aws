# Pattern-1 Confidence Threshold Enhancement

## Overview

This enhancement adds comprehensive confidence threshold support to Pattern-1 (BDA processing), enabling:

1. **UI Configuration Display** - Show confidence threshold settings in the Pattern-1 config section
2. **Dynamic Threshold Updates** - Allow real-time threshold adjustments
3. **Visual Confidence Feedback** - Color-coded confidence display in the UI
4. **Ad-hoc HITL Invocation** - Trigger human review on-demand

## Key Differences from Pattern-2

| Aspect | Pattern-2 | Pattern-1 |
|--------|-----------|-----------|
| Confidence Type | Attribute-level | Overall (Blueprint + Key-Value) |
| Threshold Scope | Per field | Single threshold for entire document |
| Display Style | Field-by-field highlighting | Overall confidence summary |
| HITL Trigger | Individual field confidence | Combined confidence assessment |

## Implementation Components

### 1. Configuration Enhancement

**File**: `config_library/pattern-1/default/config.yaml`

Added sections:
- `confidence`: Overall threshold configuration
- `hitl`: Human-in-the-loop settings
- `ui_display`: UI presentation parameters

### 2. UI Configuration Schema

**File**: `config_library/pattern-1/default/ui/config.json`

Defines:
- Confidence threshold slider (0.0 - 1.0)
- HITL enable/disable toggle
- Summarization model selection
- Temperature control

### 3. Pattern-1 Confidence Utilities

**File**: `src/ui/src/components/common/pattern1-confidence-utils.js`

Key functions:
- `getPattern1ConfidenceInfo()` - Extract overall confidence data
- `getPattern1ConfidenceSummary()` - Generate confidence summary
- `shouldTriggerHITL()` - Determine HITL necessity
- `formatConfidenceScore()` - Format confidence for display

### 4. React Components

**Files**: 
- `src/ui/src/components/pattern1/Pattern1ConfidenceDisplay.jsx`
- `src/ui/src/components/pattern1/Pattern1ConfidenceDisplay.css`

Features:
- Expandable confidence summary
- Color-coded confidence levels
- HITL trigger button
- Responsive design

### 5. HITL Service Integration

**Files**:
- `src/lambda/hitl_invocation/index.py` - Lambda for HITL triggering
- `src/ui/src/services/hitlService.js` - Frontend HITL service

## Confidence Assessment Logic

Pattern-1 uses **overall confidence** calculated as:

```javascript
overallConfidence = Math.min(
  blueprintConfidence,
  ...keyValueConfidences
)
```

HITL is triggered when:
- Blueprint confidence < threshold, OR
- Any key-value confidence < threshold

## Color Coding System

| Confidence Level | Color | Condition |
|------------------|-------|-----------|
| High | Green (#16794d) | >= threshold |
| Medium | Orange (#ff9500) | >= threshold * 0.8 |
| Low | Red (#d13313) | < threshold * 0.8 |

## API Integration

### HITL Trigger Endpoint
```
POST /trigger-hitl
{
  "document_id": "doc-123",
  "confidence_threshold": 0.8,
  "force_hitl": false
}
```

### Response
```json
{
  "message": "HITL workflow triggered successfully",
  "document_id": "doc-123",
  "hitl_job_id": "hitl-doc-123-1234567890",
  "confidence_threshold": 0.8
}
```

## Integration Steps

### 1. CloudFormation Template Updates

Add to `patterns/pattern-1/template.yaml`:

```yaml
Parameters:
  Pattern1BDAConfidenceThreshold:
    Type: Number
    Default: 0.8
    MinValue: 0.1
    MaxValue: 1.0
    Description: "Confidence threshold for Pattern-1 BDA processing"

Resources:
  HITLInvocationFunction:
    Type: AWS::Serverless::Function
    Properties:
      CodeUri: ../../src/lambda/hitl_invocation/
      Handler: index.lambda_handler
      Runtime: python3.11
      Environment:
        Variables:
          DOCUMENT_TABLE: !Ref DocumentTable
          CONFIDENCE_THRESHOLD: !Ref Pattern1BDAConfidenceThreshold
```

### 2. UI Component Integration

Update document viewer to use Pattern-1 confidence display:

```jsx
import Pattern1ConfidenceDisplay from '../pattern1/Pattern1ConfidenceDisplay';
import { triggerHITL } from '../../services/hitlService';

// In document viewer component
{document.pattern === 'pattern-1' && (
  <Pattern1ConfidenceDisplay
    document={document}
    confidenceThreshold={configThreshold}
    onTriggerHITL={triggerHITL}
  />
)}
```

### 3. Configuration Service Updates

Update configuration loading to handle Pattern-1 threshold:

```javascript
const loadPattern1Config = async () => {
  const config = await loadConfiguration('pattern-1');
  return {
    ...config,
    confidenceThreshold: config.confidence?.overall_threshold || 0.8,
    hitlEnabled: config.hitl?.enabled || true
  };
};
```

## Testing Scenarios

### 1. Threshold Configuration
- [ ] Threshold slider appears in Pattern-1 config
- [ ] Values update in real-time
- [ ] Validation prevents invalid ranges

### 2. Confidence Display
- [ ] Overall confidence shows correctly
- [ ] Color coding matches confidence level
- [ ] Blueprint and key-value details expand

### 3. HITL Triggering
- [ ] Automatic HITL when confidence < threshold
- [ ] Manual HITL trigger button works
- [ ] HITL status updates in UI

### 4. Dynamic Updates
- [ ] Threshold changes affect confidence display
- [ ] HITL trigger conditions update
- [ ] Configuration persists across sessions

## Benefits

1. **Unified Experience** - Consistent confidence handling across patterns
2. **Flexible Thresholds** - Dynamic adjustment without redeployment
3. **Visual Feedback** - Clear confidence indicators for users
4. **On-demand HITL** - Manual review triggering capability
5. **Cost Optimization** - Precise control over human review costs

## Future Enhancements

1. **Confidence Trends** - Historical confidence tracking
2. **Batch HITL** - Multiple document review workflows
3. **Custom Thresholds** - Per-document-type thresholds
4. **ML Feedback** - Confidence model improvement based on HITL results
