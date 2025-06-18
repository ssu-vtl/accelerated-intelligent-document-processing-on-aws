# HITL A2I Terminology Updates

## Overview

Updated the frontend UI to change "HITL Review" and "HITL Status" to "HITL A2I Review" and "HITL A2I Status" for clearer differentiation of Amazon Augmented AI (A2I) service usage.

## Files Updated

### 1. Document List Table Configuration
**File**: `src/ui/src/components/document-list/documents-table-config.js`

**Changes**:
- Column header: `HITL Status` → `HITL A2I Status`
- Column header: `HITL Review` → `HITL A2I Review`
- Filter labels: Updated to match new terminology
- Link text: `Review Document` → `Review in A2I`
- Aria label: `Opens in a new tab` → `Opens A2I review in a new tab`

### 2. Document Panel Component
**File**: `src/ui/src/components/document-panel/DocumentPanel.jsx`

**Changes**:
- Status label: `HITL Status` → `HITL A2I Status`
- Button text: `Review Document` → `Review Document in A2I`

### 3. Pattern-1 Confidence Display Component
**File**: `src/ui/src/components/pattern1/Pattern1ConfidenceDisplay.jsx`

**Changes**:
- Button text: `Trigger Human Review` → `Trigger A2I Human Review`
- Loading text: `Triggering...` → `Triggering A2I Review...`
- Indicator text: `HITL Triggered` → `A2I Review Triggered`

### 4. Pattern-1 Confidence Display Styles
**File**: `src/ui/src/components/pattern1/Pattern1ConfidenceDisplay.css`

**Changes**:
- Added CSS comments to clarify A2I usage
- Updated section comments for A2I trigger actions and button styles

### 5. HITL Service
**File**: `src/ui/src/services/hitlService.js`

**Changes**:
- Service description: `HITL (Human In The Loop) operations` → `HITL A2I (Human In The Loop with Amazon Augmented AI) operations`

### 6. Pattern-1 Configuration Files
**File**: `config_library/pattern-1/default/config.yaml`

**Changes**:
- Description: `avoid human review` → `avoid A2I human review`
- HITL description: `Human In The Loop configuration` → `Human In The Loop A2I configuration`

**File**: `config_library/pattern-1/default/ui/config.json`

**Changes**:
- Display name: `BDA Processing with HITL` → `BDA Processing with HITL A2I`
- Description: `Human In The Loop support` → `Human In The Loop A2I support`
- Section title: `Confidence & HITL Settings` → `Confidence & HITL A2I Settings`
- Section description: `human review settings` → `A2I human review settings`
- Field label: `Enable Human In The Loop` → `Enable HITL A2I`
- Field description: `sent for human review` → `sent for A2I human review`
- Threshold description: `avoid human review` → `avoid A2I human review`

## UI Impact

### Before
- Column headers: "HITL Status", "HITL Review"
- Button text: "Review Document", "Trigger Human Review"
- Status indicators: "HITL Triggered"
- Configuration labels: "Enable Human In The Loop"

### After
- Column headers: "HITL A2I Status", "HITL A2I Review"
- Button text: "Review Document in A2I", "Trigger A2I Human Review"
- Status indicators: "A2I Review Triggered"
- Configuration labels: "Enable HITL A2I"

## Benefits

1. **Clear Service Identification**: Users immediately understand that Amazon A2I is being used
2. **Consistent Terminology**: All HITL references now explicitly mention A2I
3. **Better User Experience**: More descriptive labels help users understand the workflow
4. **Documentation Alignment**: UI terminology matches AWS service documentation

## Testing Checklist

- [ ] Document list table shows "HITL A2I Status" and "HITL A2I Review" columns
- [ ] Document panel displays "HITL A2I Status" label
- [ ] Review buttons show "Review Document in A2I" text
- [ ] Pattern-1 confidence display shows "Trigger A2I Human Review" button
- [ ] Configuration UI shows "Enable HITL A2I" toggle
- [ ] All tooltips and aria-labels reference A2I appropriately
- [ ] Loading states show "Triggering A2I Review..." text
- [ ] Status indicators show "A2I Review Triggered"

## Backward Compatibility

These changes are purely cosmetic and do not affect:
- API endpoints or data structures
- Backend processing logic
- Database schemas
- Configuration file structure (only display labels changed)

The underlying functionality remains identical - only the user-facing terminology has been updated for clarity.
