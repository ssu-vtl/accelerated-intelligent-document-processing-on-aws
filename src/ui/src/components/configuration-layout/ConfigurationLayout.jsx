import React, { useState, useEffect, useRef } from 'react';
import {
  Container,
  Header,
  SpaceBetween,
  Box,
  Button,
  Alert,
  Spinner,
  Form,
  SegmentedControl,
} from '@awsui/components-react';
import Editor from '@monaco-editor/react';
// eslint-disable-next-line import/no-extraneous-dependencies
import yaml from 'js-yaml';
import useConfiguration from '../../hooks/use-configuration';
import FormView from './FormView';

const ConfigurationLayout = () => {
  const { schema, mergedConfig, loading, error, updateConfiguration, fetchConfiguration } = useConfiguration();

  const [formValues, setFormValues] = useState({});
  const [jsonContent, setJsonContent] = useState('');
  const [yamlContent, setYamlContent] = useState('');
  const [isSaving, setIsSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [saveError, setSaveError] = useState(null);
  const [validationErrors, setValidationErrors] = useState([]);
  const [viewMode, setViewMode] = useState('form'); // Form view as default

  const editorRef = useRef(null);

  // Initialize form values from merged config
  useEffect(() => {
    if (mergedConfig) {
      console.log('Setting form values from mergedConfig:', mergedConfig);

      // Make a deep copy to ensure we're not dealing with references
      const formData = JSON.parse(JSON.stringify(mergedConfig));
      setFormValues(formData);

      // Set both JSON and YAML content
      const jsonString = JSON.stringify(mergedConfig, null, 2);
      setJsonContent(jsonString);

      try {
        const yamlString = yaml.dump(mergedConfig);
        setYamlContent(yamlString);
      } catch (e) {
        console.error('Error converting to YAML:', e);
        setYamlContent('# Error converting to YAML');
      }
    }
  }, [mergedConfig]);

  const handleEditorDidMount = (editor, monaco) => {
    editorRef.current = editor;

    // Set up JSON schema validation if schema is available and in JSON mode
    if (schema && viewMode === 'json') {
      try {
        // Convert schema to proper JSON Schema format if needed
        const jsonSchema = {
          uri: 'http://myserver/schema.json',
          fileMatch: ['*'],
          schema: {
            type: 'object',
            properties: schema.properties || {},
            required: schema.required || [],
          },
        };

        monaco.languages.json.jsonDefaults.setDiagnosticsOptions({
          validate: true,
          schemas: [jsonSchema],
          allowComments: false,
          trailingCommas: 'error',
        });
      } catch (e) {
        console.error('Error setting up schema validation:', e);
      }
    }
  };

  // Handle changes in the JSON editor
  const handleJsonEditorChange = (value) => {
    setJsonContent(value);
    try {
      const parsedValue = JSON.parse(value);
      setFormValues(parsedValue);

      // Update YAML when JSON changes
      try {
        const yamlString = yaml.dump(parsedValue);
        setYamlContent(yamlString);
      } catch (yamlErr) {
        console.error('Error converting to YAML:', yamlErr);
      }

      setValidationErrors([]);
    } catch (e) {
      setValidationErrors([{ message: `Invalid JSON: ${e.message}` }]);
    }
  };

  // Handle changes in the YAML editor
  const handleYamlEditorChange = (value) => {
    setYamlContent(value);
    try {
      const parsedValue = yaml.load(value);
      setFormValues(parsedValue);

      // Update JSON when YAML changes
      try {
        const jsonString = JSON.stringify(parsedValue, null, 2);
        setJsonContent(jsonString);
      } catch (jsonErr) {
        console.error('Error converting to JSON:', jsonErr);
      }

      setValidationErrors([]);
    } catch (e) {
      setValidationErrors([{ message: `Invalid YAML: ${e.message}` }]);
    }
  };

  const handleSave = async () => {
    if (validationErrors.length > 0) {
      setSaveError('Cannot save: Configuration contains validation errors');
      return;
    }

    setIsSaving(true);
    setSaveSuccess(false);
    setSaveError(null);

    try {
      // Save to backend
      const success = await updateConfiguration(formValues);

      if (success) {
        setSaveSuccess(true);
        // Force a refresh of the configuration to ensure UI is in sync with backend
        setTimeout(() => {
          fetchConfiguration();
        }, 1000);
      } else {
        setSaveError('Failed to save configuration. Please try again.');
      }
    } catch (err) {
      console.error('Save error:', err);
      setSaveError(`Error: ${err.message}`);
    } finally {
      setIsSaving(false);
    }
  };

  const handleFormChange = (newValues) => {
    setFormValues(newValues);
    try {
      // Update both JSON and YAML content
      const jsonString = JSON.stringify(newValues, null, 2);
      setJsonContent(jsonString);

      try {
        const yamlString = yaml.dump(newValues);
        setYamlContent(yamlString);
      } catch (yamlErr) {
        console.error('Error converting to YAML:', yamlErr);
      }

      setValidationErrors([]);
    } catch (e) {
      setValidationErrors([{ message: `Error converting form values to JSON: ${e.message}` }]);
    }
  };

  const formatJson = () => {
    if (editorRef.current && viewMode === 'json') {
      editorRef.current.getAction('editor.action.formatDocument').run();
    }
  };

  const formatYaml = () => {
    if (editorRef.current && viewMode === 'yaml') {
      editorRef.current.getAction('editor.action.formatDocument').run();
    }
  };

  if (loading) {
    return (
      <Container header={<Header variant="h2">Configuration</Header>}>
        <Box textAlign="center" padding="l">
          <Spinner size="large" />
          <Box padding="s">Loading configuration...</Box>
        </Box>
      </Container>
    );
  }

  if (error) {
    return (
      <Container header={<Header variant="h2">Configuration</Header>}>
        <Alert type="error" header="Error loading configuration">
          {error}
          <Button onClick={fetchConfiguration} variant="primary" style={{ marginTop: '1rem' }}>
            Retry
          </Button>
        </Alert>
      </Container>
    );
  }

  if (!schema || !mergedConfig) {
    return (
      <Container header={<Header variant="h2">Configuration</Header>}>
        <Alert type="error" header="Configuration not available">
          Unable to load configuration schema or values.
          <Button onClick={fetchConfiguration} variant="primary" style={{ marginTop: '1rem' }}>
            Retry
          </Button>
        </Alert>
      </Container>
    );
  }

  return (
    <Container
      header={
        <Header
          variant="h2"
          actions={
            <SpaceBetween direction="horizontal" size="xs">
              <SegmentedControl
                selectedId={viewMode}
                onChange={({ detail }) => setViewMode(detail.selectedId)}
                options={[
                  { id: 'form', text: 'Form View' },
                  { id: 'json', text: 'JSON View' },
                  { id: 'yaml', text: 'YAML View' },
                ]}
              />
              {viewMode === 'json' && (
                <Button onClick={formatJson} iconName="file-text">
                  Format JSON
                </Button>
              )}
              {viewMode === 'yaml' && (
                <Button onClick={formatYaml} iconName="file-text">
                  Format YAML
                </Button>
              )}
              <Button variant="primary" onClick={handleSave} loading={isSaving}>
                Save changes
              </Button>
            </SpaceBetween>
          }
        >
          Configuration
        </Header>
      }
    >
      <Form>
        {saveSuccess && (
          <Alert
            type="success"
            dismissible
            onDismiss={() => setSaveSuccess(false)}
            header="Configuration saved successfully"
          >
            Your configuration changes have been saved.
          </Alert>
        )}

        {saveError && (
          <Alert type="error" dismissible onDismiss={() => setSaveError(null)} header="Error saving configuration">
            {saveError}
          </Alert>
        )}

        {validationErrors.length > 0 && (
          <Alert type="warning" header="Validation errors">
            <ul>
              {validationErrors.map((e, index) => (
                // eslint-disable-next-line react/no-array-index-key
                <li key={index}>{e.message}</li>
              ))}
            </ul>
          </Alert>
        )}

        <Box padding="s">
          {viewMode === 'form' && <FormView schema={schema} formValues={formValues} onChange={handleFormChange} />}

          {viewMode === 'json' && (
            <Editor
              height="70vh"
              defaultLanguage="json"
              value={jsonContent}
              onChange={handleJsonEditorChange}
              onMount={handleEditorDidMount}
              options={{
                minimap: { enabled: false },
                formatOnPaste: true,
                formatOnType: true,
                automaticLayout: true,
                scrollBeyondLastLine: false,
                folding: true,
                lineNumbers: 'on',
                renderLineHighlight: 'all',
                tabSize: 2,
              }}
            />
          )}

          {viewMode === 'yaml' && (
            <Editor
              height="70vh"
              defaultLanguage="yaml"
              value={yamlContent}
              onChange={handleYamlEditorChange}
              onMount={handleEditorDidMount}
              options={{
                minimap: { enabled: false },
                formatOnPaste: true,
                formatOnType: true,
                automaticLayout: true,
                scrollBeyondLastLine: false,
                folding: true,
                lineNumbers: 'on',
                renderLineHighlight: 'all',
                tabSize: 2,
              }}
            />
          )}
        </Box>
      </Form>
    </Container>
  );
};

export default ConfigurationLayout;
