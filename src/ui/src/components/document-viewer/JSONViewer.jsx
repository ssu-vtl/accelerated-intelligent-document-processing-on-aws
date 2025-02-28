/* eslint-disable react/prop-types */
import React, { useState, useRef, useEffect } from 'react';
import { Box, SpaceBetween, Button, Toggle } from '@awsui/components-react';
import { API, Logger } from 'aws-amplify';
import { Editor } from '@monaco-editor/react';
import getFileContents from '../../graphql/queries/getFileContents';
import uploadDocument from '../../graphql/queries/uploadDocument';

const logger = new Logger('FileEditor');

const EDITOR_DEFAULT_HEIGHT = '600px';

const FileEditorView = ({ fileContent, onChange, isReadOnly = true, fileType = 'text' }) => {
  const [isValid, setIsValid] = useState(true);
  const [isEditorReady, setIsEditorReady] = useState(false);
  const editorRef = useRef(null);
  const containerRef = useRef(null);

  useEffect(() => {
    let timeoutId;
    if (isEditorReady) {
      timeoutId = setTimeout(() => {
        if (editorRef.current) {
          editorRef.current.layout();
        }
      }, 100);
    }
    return () => {
      if (timeoutId) {
        clearTimeout(timeoutId);
      }
    };
  }, [isEditorReady]);

  const handleEditorDidMount = (editor) => {
    editorRef.current = editor;
    // Set initial layout
    editor.layout();
    setIsEditorReady(true);
  };

  const handleEditorChange = (value) => {
    if (fileType === 'json') {
      try {
        JSON.parse(value);
        setIsValid(true);
        if (onChange) {
          onChange(value);
        }
      } catch (error) {
        setIsValid(false);
        logger.error('Invalid JSON:', error);
      }
    } else {
      setIsValid(true);
      if (onChange) {
        onChange(value);
      }
    }
  };

  const formatContent = (rawContent) => {
    if (fileType === 'json') {
      try {
        const parsed = JSON.parse(rawContent);
        return JSON.stringify(parsed, null, 2);
      } catch (error) {
        logger.error('Error formatting JSON:', error);
        return rawContent;
      }
    }
    return rawContent;
  };

  return (
    <Box
      className="file-editor-container"
      style={{ border: `2px solid ${isValid ? '#e9ebed' : '#d13212'}` }}
      ref={containerRef}
    >
      <div
        style={{
          height: EDITOR_DEFAULT_HEIGHT,
          position: 'relative',
          overflow: 'hidden',
        }}
      >
        <Editor
          height="100%"
          defaultLanguage={fileType}
          value={formatContent(fileContent)}
          onChange={handleEditorChange}
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
      {!isValid && (
        <Box color="text-status-error" padding="s">
          Invalid {fileType.toUpperCase()} format
        </Box>
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
