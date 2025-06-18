# Pattern-1 Confidence Enhancement - Implementation Guide

## Quick Start

### 1. Verify Files Created
```bash
# Check configuration files
ls -la config_library/pattern-1/default/
ls -la config_library/pattern-1/default/ui/

# Check UI components
ls -la src/ui/src/components/pattern1/
ls -la src/ui/src/components/common/pattern1-confidence-utils.js

# Check Lambda function
ls -la src/lambda/hitl_invocation/

# Check service
ls -la src/ui/src/services/hitlService.js
```

### 2. Update CloudFormation Template

Add to `patterns/pattern-1/template.yaml`:

```yaml
# In Parameters section
Pattern1BDAConfidenceThreshold:
  Type: Number
  Default: 0.8
  MinValue: 0.1
  MaxValue: 1.0
  Description: "Confidence threshold for Pattern-1 BDA processing"

# In Resources section  
HITLInvocationFunction:
  Type: AWS::Serverless::Function
  Properties:
    CodeUri: ../../src/lambda/hitl_invocation/
    Handler: index.lambda_handler
    Runtime: python3.11
    Timeout: 300
    Environment:
      Variables:
        DOCUMENT_TABLE: !Ref DocumentTable
        LOG_LEVEL: !Ref LogLevel
    Events:
      HITLApi:
        Type: Api
        Properties:
          Path: /trigger-hitl
          Method: post
          RestApiId: !Ref WebUIApi
```

### 3. Update UI Configuration Loading

In `src/ui/src/services/configurationService.js`, add:

```javascript
export const loadPattern1Configuration = async () => {
  try {
    const response = await fetch('/api/configuration/pattern-1');
    const config = await response.json();
    
    return {
      ...config,
      confidenceThreshold: config.confidence?.overall_threshold || 0.8,
      hitlEnabled: config.hitl?.enabled || true,
      uiDisplay: config.confidence?.ui_display || {}
    };
  } catch (error) {
    console.error('Error loading Pattern-1 configuration:', error);
    throw error;
  }
};
```

### 4. Integrate Confidence Display

In your document viewer component:

```jsx
import Pattern1ConfidenceDisplay from '../pattern1/Pattern1ConfidenceDisplay';
import { triggerHITL } from '../../services/hitlService';

const DocumentViewer = ({ document, configuration }) => {
  const handleTriggerHITL = async (documentId, threshold) => {
    try {
      const result = await triggerHITL(documentId, threshold);
      // Handle success - maybe show notification
      console.log('HITL triggered:', result);
    } catch (error) {
      // Handle error - show error message
      console.error('HITL trigger failed:', error);
    }
  };

  return (
    <div className="document-viewer">
      {/* Other document content */}
      
      {document.pattern === 'pattern-1' && (
        <Pattern1ConfidenceDisplay
          document={document}
          confidenceThreshold={configuration.confidenceThreshold}
          onTriggerHITL={handleTriggerHITL}
        />
      )}
    </div>
  );
};
```

### 5. Update Configuration UI

In your configuration management component:

```jsx
import { loadPattern1Configuration } from '../services/configurationService';

const Pattern1ConfigSection = () => {
  const [config, setConfig] = useState(null);
  const [threshold, setThreshold] = useState(0.8);

  useEffect(() => {
    loadPattern1Configuration().then(setConfig);
  }, []);

  const handleThresholdChange = (newThreshold) => {
    setThreshold(newThreshold);
    // Update configuration
    updateConfiguration('pattern-1', {
      ...config,
      confidence: {
        ...config.confidence,
        overall_threshold: newThreshold
      }
    });
  };

  return (
    <div className="pattern1-config">
      <h3>Pattern-1 Configuration</h3>
      
      <div className="config-field">
        <label>Confidence Threshold</label>
        <input
          type="range"
          min="0.1"
          max="1.0"
          step="0.05"
          value={threshold}
          onChange={(e) => handleThresholdChange(parseFloat(e.target.value))}
        />
        <span>{(threshold * 100).toFixed(0)}%</span>
      </div>
    </div>
  );
};
```

## Testing the Implementation

### 1. Test Configuration Display
```bash
# Deploy the stack
sam build && sam deploy

# Check if configuration loads
curl -X GET "https://your-api-gateway/api/configuration/pattern-1"
```

### 2. Test Confidence Display
- Upload a Pattern-1 document
- Verify confidence information appears
- Check color coding matches confidence levels
- Test expand/collapse functionality

### 3. Test HITL Triggering
```bash
# Test HITL API directly
curl -X POST "https://your-api-gateway/api/trigger-hitl" \
  -H "Content-Type: application/json" \
  -d '{
    "document_id": "test-doc-id",
    "confidence_threshold": 0.8,
    "force_hitl": false
  }'
```

### 4. Test Dynamic Threshold Updates
- Change threshold in configuration UI
- Verify confidence display updates
- Check HITL trigger conditions change

## Troubleshooting

### Common Issues

1. **Configuration not loading**
   - Check API Gateway endpoints
   - Verify Lambda permissions
   - Check CloudWatch logs

2. **Confidence display not showing**
   - Verify document has explainability_info
   - Check confidence data structure
   - Ensure Pattern-1 utilities are imported

3. **HITL not triggering**
   - Check Lambda function deployment
   - Verify DynamoDB permissions
   - Check confidence threshold logic

### Debug Commands

```bash
# Check Lambda logs
aws logs tail /aws/lambda/your-hitl-function --follow

# Check API Gateway logs
aws logs tail API-Gateway-Execution-Logs_your-api-id/prod --follow

# Test configuration loading
aws dynamodb get-item \
  --table-name your-config-table \
  --key '{"id":{"S":"pattern-1"}}'
```

## Performance Considerations

1. **Confidence Calculation** - Cached for performance
2. **API Calls** - Debounced threshold updates
3. **UI Updates** - Optimized re-renders
4. **Lambda Cold Starts** - Provisioned concurrency if needed

## Security Notes

1. **API Authentication** - Ensure proper auth on HITL endpoints
2. **Input Validation** - Validate threshold ranges
3. **CORS Configuration** - Proper CORS headers for UI calls
4. **IAM Permissions** - Least privilege for Lambda functions
