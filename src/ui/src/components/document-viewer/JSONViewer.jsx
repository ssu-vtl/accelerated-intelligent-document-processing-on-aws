/* eslint-disable react/prop-types */
import React, { useState, useEffect } from 'react';
import { Box, SpaceBetween, Button, Toggle, Alert } from '@awsui/components-react';
import { API, Logger } from 'aws-amplify';
import { Editor } from '@monaco-editor/react';
import getFileContents from '../../graphql/queries/getFileContents';
import uploadDocument from '../../graphql/queries/uploadDocument';

const logger = new Logger('FileEditor');

const EDITOR_DEFAULT_HEIGHT = '600px';

// Import the necessary packages in package.json before using:
// npm install --save react-json-view

// Lazy load the JsonView component to avoid importing it if not needed
const ReactJsonView = React.lazy(() => import('react-json-view'));

const JsonEditorView = ({ jsonData, onChange, isReadOnly }) => {
  return (
    <Box
      style={{
        height: EDITOR_DEFAULT_HEIGHT,
        position: 'relative',
        overflow: 'auto',
        padding: '10px',
        backgroundColor: '#f8f8f8',
        border: '2px solid #e9ebed',
        borderRadius: '4px',
      }}
    >
      <React.Suspense fallback={<Box padding="s">Loading JSON editor...</Box>}>
        <ReactJsonView
          src={jsonData}
          name={false}
          theme="rjv-default"
          collapsed={false}
          displayDataTypes={false}
          enableClipboard={false}
          onEdit={isReadOnly ? false : onChange}
          onAdd={isReadOnly ? false : onChange}
          onDelete={isReadOnly ? false : onChange}
          style={{ fontSize: '14px' }}
        />
      </React.Suspense>
    </Box>
  );
};

const TextEditorView = ({ fileContent, onChange, isReadOnly, fileType }) => {
  const [isEditorReady, setIsEditorReady] = useState(false);

  useEffect(() => {
    let timeoutId;
    if (isEditorReady) {
      timeoutId = setTimeout(() => {
        if (window.monacoEditor) {
          window.monacoEditor.layout();
        }
      }, 100);
    }
    return () => {
      if (timeoutId) clearTimeout(timeoutId);
    };
  }, [isEditorReady]);

  const handleEditorDidMount = (editor) => {
    window.monacoEditor = editor;
    editor.layout();
    setIsEditorReady(true);
  };

  return (
    <Box className="file-editor-container" style={{ border: '2px solid #e9ebed' }}>
      <div style={{ height: EDITOR_DEFAULT_HEIGHT, position: 'relative', overflow: 'hidden' }}>
        <Editor
          height="100%"
          defaultLanguage={fileType}
          value={fileContent}
          onChange={onChange}
          onMount={handleEditorDidMount}
          options={{
            readOnly: isReadOnly,
            minimap: { enabled: false },
            fontSize: 14,
            wordWrap: 'on',
            wrappingIndent: 'indent',
            automaticLayout: false,
            scrollBeyondLastLine: false,
            fixedOverflowWidgets: true,
            scrollbar: {
              vertical: 'visible',
              horizontal: 'visible',
            },
          }}
          theme="vs-light"
          loading={<Box padding="s">Loading editor...</Box>}
        />
      </div>
    </Box>
  );
};

const FileEditorView = ({ fileContent, onChange, isReadOnly = true, fileType = 'text' }) => {
  const [isValid, setIsValid] = useState(true);
  const [jsonData, setJsonData] = useState(null);
  const [viewMode, setViewMode] = useState('structured');

  useEffect(() => {
    if (fileType === 'json') {
      try {
        const parsed = typeof fileContent === 'string' ? JSON.parse(fileContent) : fileContent;
        setJsonData(parsed);
        setIsValid(true);
      } catch (error) {
        setIsValid(false);
        logger.error('Invalid JSON:', error);
      }
    }
  }, [fileContent, fileType]);

  const handleJsonEditorChange = (edit) => {
    try {
      // Update the JSON data
      setJsonData(edit.updated_src);
      setIsValid(true);

      // Convert to string for the onChange handler
      const jsonString = JSON.stringify(edit.updated_src, null, 2);
      if (onChange) {
        onChange(jsonString);
      }
    } catch (error) {
      setIsValid(false);
      logger.error('Error updating JSON:', error);
    }
  };

  const handleTextEditorChange = (value) => {
    if (fileType === 'json') {
      try {
        const parsed = JSON.parse(value);
        setJsonData(parsed);
        setIsValid(true);
        if (onChange) {
          onChange(value);
        }
      } catch (error) {
        setIsValid(false);
        logger.error('Invalid JSON:', error);
      }
    } else if (onChange) {
      onChange(value);
    }
  };

  const toggleViewMode = () => {
    setViewMode(viewMode === 'structured' ? 'text' : 'structured');
  };

  if (fileType !== 'json') {
    return (
      <TextEditorView
        fileContent={fileContent}
        onChange={handleTextEditorChange}
        isReadOnly={isReadOnly}
        fileType={fileType}
      />
    );
  }

  return (
    <Box>
      {fileType === 'json' && (
        <SpaceBetween direction="horizontal" size="xs" alignItems="center">
          <Button onClick={toggleViewMode} variant="link">
            Switch to {viewMode === 'structured' ? 'text' : 'structured'} view
          </Button>
        </SpaceBetween>
      )}

      {!isValid && (
        <Alert type="error" header="Invalid JSON format">
          The JSON content is invalid. Please correct any syntax errors.
        </Alert>
      )}

      {viewMode === 'structured' && isValid && fileType === 'json' ? (
        <JsonEditorView jsonData={jsonData} onChange={handleJsonEditorChange} isReadOnly={isReadOnly} />
      ) : (
        <TextEditorView
          fileContent={typeof fileContent === 'string' ? fileContent : JSON.stringify(fileContent, null, 2)}
          onChange={handleTextEditorChange}
          isReadOnly={isReadOnly}
          fileType={fileType}
        />
      )}
    </Box>
  );
};

const JSONViewer = ({ fileUri, fileType = 'text', buttonText = 'View File' }) => {
  const [fileContent, setFileContent] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [isEditing, setIsEditing] = useState(false);
  const [editedContent, setEditedContent] = useState(null);

  const fetchContent = async () => {
    setIsLoading(true);
    setError(null);
    try {
      logger.info('Fetching content:', fileUri);

      const response = await API.graphql({
        query: getFileContents,
        variables: { s3Uri: fileUri },
      });

      const fetchedContent = response.data.getFileContents;
      logger.debug('Received content:', `${fetchedContent.substring(0, 100)}...`);

      setFileContent(fetchedContent);
    } catch (err) {
      logger.error('Error fetching content:', err);
      setError(`Failed to load ${fileType} content. Please try again.`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleEditToggle = ({ detail }) => {
    setIsEditing(detail.checked);
    if (detail.checked && !editedContent) {
      setEditedContent(fileContent);
    }
  };

  const handleContentChange = (newContent) => {
    setEditedContent(newContent);
  };

  const handleSave = async () => {
    try {
      logger.info('Saving changes to file:', fileUri);

      // Parse the S3 URI to get the correct path
      const s3UriMatch = fileUri.match(/^s3:\/\/([^/]+)\/(.+)$/);
      if (!s3UriMatch) {
        throw new Error('Invalid S3 URI format');
      }

      const [, bucket, fullPath] = s3UriMatch;
      const fileName = fullPath.split('/').pop();
      const prefix = fullPath.substring(0, fullPath.lastIndexOf('/'));

      // Get presigned URL
      const response = await API.graphql({
        query: uploadDocument,
        variables: {
          fileName,
          contentType: 'application/json',
          prefix,
          bucket,
        },
      });

      const { presignedUrl, usePostMethod } = response.data.uploadDocument;

      if (!usePostMethod) {
        throw new Error('Server returned PUT method which is not supported');
      }

      // Parse the presigned post data
      const presignedPostData = JSON.parse(presignedUrl);

      // Create form data
      const formData = new FormData();

      // Add all fields from presigned POST data
      Object.entries(presignedPostData.fields).forEach(([key, value]) => {
        formData.append(key, value);
      });

      // Create a Blob from the JSON content and append it as a file
      const blob = new Blob([editedContent], { type: 'application/json' });
      formData.append('file', blob, fileName);

      // Upload to S3
      const uploadResponse = await fetch(presignedPostData.url, {
        method: 'POST',
        body: formData,
      });

      if (!uploadResponse.ok) {
        const errorText = await uploadResponse.text().catch(() => 'Could not read error response');
        throw new Error(`Upload failed: ${errorText}`);
      }

      // Update the file content state to reflect saved changes
      setFileContent(editedContent);
      setIsEditing(false);
      setSuccess('File saved and uploaded successfully');
      logger.info('Successfully saved changes');

      // Clear success message after 3 seconds
      setTimeout(() => {
        setSuccess(null);
      }, 3000);
    } catch (err) {
      logger.error('Error saving changes:', err);
      setError(`Failed to save changes: ${err.message}`);
    }
  };

  const closeViewer = () => {
    setFileContent(null);
    setEditedContent(null);
    setIsEditing(false);
  };

  if (!fileUri) {
    return (
      <Box color="text-status-inactive" padding={{ top: 's' }}>
        File content not available
      </Box>
    );
  }

  return (
    <Box className="w-full">
      {!fileContent && (
        <Button onClick={fetchContent} loading={isLoading} disabled={isLoading}>
          {buttonText}
        </Button>
      )}

      {error && (
        <Box color="text-status-error" padding="s">
          {error}
        </Box>
      )}

      {success && (
        <Box color="text-status-success" padding="s">
          {success}
        </Box>
      )}

      {fileContent && (
        <SpaceBetween size="s">
          <Box>
            <SpaceBetween direction="horizontal" size="xs">
              <Button onClick={closeViewer}>Close</Button>
              <Toggle onChange={handleEditToggle} checked={isEditing}>
                Edit mode
              </Toggle>
              {isEditing && (
                <Button
                  variant="primary"
                  onClick={handleSave}
                  disabled={!editedContent || editedContent === fileContent}
                >
                  Save Changes
                </Button>
              )}
            </SpaceBetween>
          </Box>
          <FileEditorView
            fileContent={isEditing ? editedContent : fileContent}
            onChange={handleContentChange}
            isReadOnly={!isEditing}
            fileType={fileType}
          />
        </SpaceBetween>
      )}
    </Box>
  );
};

export default JSONViewer;
