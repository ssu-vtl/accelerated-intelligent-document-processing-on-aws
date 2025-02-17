/* eslint-disable react/prop-types */
import React, { useState, useRef, useEffect } from 'react';
import { Box, SpaceBetween, Button, Toggle } from '@awsui/components-react';
import { API, Logger } from 'aws-amplify';
import { Editor } from '@monaco-editor/react';
import getFileContents from '../../graphql/queries/getFileContents';

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

const FileViewer = ({ fileUri, fileType = 'text', buttonText = 'View File' }) => {
  const [fileContent, setFileContent] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
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
    // TODO: Implement save functionality
    logger.info('Save functionality to be implemented');
    alert('Save functionality coming soon!');
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

export default FileViewer;
