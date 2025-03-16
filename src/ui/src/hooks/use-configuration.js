import { useState, useEffect } from 'react';
import { API, graphqlOperation, Logger } from 'aws-amplify';
import getConfigurationQuery from '../graphql/queries/getConfiguration';
import updateConfigurationMutation from '../graphql/queries/updateConfiguration';

const logger = new Logger('useConfiguration');

// Deep merge function for combining default and custom configurations
const deepMerge = (target, source) => {
  const result = { ...target };

  if (!source) {
    return result;
  }

  Object.keys(source)
    .filter((key) => Object.hasOwn(source, key))
    .forEach((key) => {
      if (source[key] && typeof source[key] === 'object' && !Array.isArray(source[key])) {
        if (Object.hasOwn(target, key) && target[key] && typeof target[key] === 'object') {
          result[key] = deepMerge(target[key], source[key]);
        } else {
          result[key] = { ...source[key] };
        }
      } else {
        result[key] = source[key];
      }
    });

  return result;
};

const useConfiguration = () => {
  const [schema, setSchema] = useState(null);
  const [defaultConfig, setDefaultConfig] = useState(null);
  const [customConfig, setCustomConfig] = useState(null);
  const [mergedConfig, setMergedConfig] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchConfiguration = async () => {
    setLoading(true);
    setError(null);
    try {
      logger.debug('Fetching configuration...');
      const result = await API.graphql(graphqlOperation(getConfigurationQuery));
      logger.debug('API response:', result);

      const { Schema, Default, Custom } = result.data.getConfiguration;

      // Log raw data types
      logger.debug('Raw data types:', {
        Schema: typeof Schema,
        Default: typeof Default,
        Custom: typeof Custom,
      });

      // Enhanced parsing logic - handle both string and object types
      let schemaObj = Schema;
      let defaultObj = Default;
      let customObj = Custom;

      // Parse schema if it's a string
      if (typeof Schema === 'string') {
        try {
          schemaObj = JSON.parse(Schema);
          logger.debug('Schema parsed from string successfully');
        } catch (e) {
          logger.error('Error parsing schema string:', e);
          throw new Error(`Failed to parse schema data: ${e.message}`);
        }
      }

      // Parse default config if it's a string
      if (typeof Default === 'string') {
        try {
          defaultObj = JSON.parse(Default);
          logger.debug('Default config parsed from string successfully');
        } catch (e) {
          logger.error('Error parsing default config string:', e);
          throw new Error(`Failed to parse default configuration: ${e.message}`);
        }
      }

      // Parse custom config if it's a string and not null/empty
      if (typeof Custom === 'string' && Custom) {
        try {
          customObj = JSON.parse(Custom);
          logger.debug('Custom config parsed from string successfully');
        } catch (e) {
          logger.error('Error parsing custom config string:', e);
          // Don't throw here, just log the error and use empty object
          customObj = {};
        }
      } else if (!Custom) {
        customObj = {};
      }

      // Debug the parsed objects
      logger.debug('Parsed schema:', schemaObj);
      logger.debug('Parsed default config:', defaultObj);
      logger.debug('Parsed custom config:', customObj);

      // Validate the parsed objects
      if (!schemaObj || typeof schemaObj !== 'object') {
        throw new Error(`Invalid schema data structure ${typeof schemaObj}`);
      }

      if (!defaultObj || typeof defaultObj !== 'object') {
        throw new Error('Invalid default configuration data structure');
      }

      setSchema(schemaObj);
      setDefaultConfig(defaultObj);
      setCustomConfig(customObj);

      // Merge default and custom configurations
      const merged = deepMerge(defaultObj, customObj);
      console.log('Merged configuration result:', merged);
      // Double check the classification and extraction sections
      if (merged.classification) {
        console.log('Final classification data:', merged.classification);
      }
      if (merged.extraction) {
        console.log('Final extraction data:', merged.extraction);
      }
      setMergedConfig(merged);
    } catch (err) {
      logger.error('Error fetching configuration', err);
      setError(`Failed to load configuration: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const updateConfiguration = async (newCustomConfig) => {
    setError(null);
    try {
      logger.debug('Updating config with:', newCustomConfig);

      // Make sure we have a valid object to update with
      const configToUpdate =
        !newCustomConfig || (typeof newCustomConfig === 'object' && Object.keys(newCustomConfig).length === 0)
          ? {} // Use empty object fallback
          : newCustomConfig;

      if (configToUpdate !== newCustomConfig) {
        logger.warn('Attempting to update with empty configuration, using {} as fallback');
      }

      // Ensure we're sending a JSON string
      const configString = typeof configToUpdate === 'string' ? configToUpdate : JSON.stringify(configToUpdate);

      logger.debug('Sending customConfig string:', configString);

      const result = await API.graphql(graphqlOperation(updateConfigurationMutation, { customConfig: configString }));

      if (result.data.updateConfiguration) {
        setCustomConfig(configToUpdate);
        // Update merged config
        const merged = deepMerge(defaultConfig, configToUpdate);
        setMergedConfig(merged);
        return true;
      }
      return false;
    } catch (err) {
      logger.error('Error updating configuration', err);
      setError(`Failed to update configuration: ${err.message}`);
      return false;
    }
  };

  // Reset a specific configuration path back to default
  const resetToDefault = async (path) => {
    if (!customConfig || !path) return false;

    // Create a copy of the custom config
    const newCustomConfig = { ...customConfig };

    // Handle both dot notation and bracket notation
    // First, normalize the path to handle array indices properly
    const normalizedPath = path.replace(/\[(\d+)\]/g, '.$1');

    // Split the path into segments and handle array indices
    let pathSegments;

    // Check if the path already contains bracket notation for arrays
    if (path.includes('[')) {
      // Use regex to split properly on both dots and brackets
      pathSegments = normalizedPath.split('.');
    } else {
      // Regular dot notation
      pathSegments = path.split('.');
    }

    // Look for any numeric segments which indicate array indices
    const arrayIndices = [];
    pathSegments.forEach((segment, index) => {
      if (/^\d+$/.test(segment)) {
        arrayIndices.push(index);
      }
    });

    // If we found any array indices, we need to reset the entire array
    if (arrayIndices.length > 0) {
      // Get the path to the array itself (everything before the first array index)
      const firstArrayIndex = arrayIndices[0];
      const arrayPath = pathSegments.slice(0, firstArrayIndex).join('.');

      logger.debug(`Detected array item path: ${path}`);
      logger.debug(`Resetting entire array at path: ${arrayPath}`);

      // If we have a valid array path, reset it
      if (arrayPath) {
        return resetToDefault(arrayPath);
      }
    }

    // Navigate to the parent object of the value to reset
    let current = newCustomConfig;
    let parent = null;
    let lastKey = null;

    pathSegments.forEach((segment, index) => {
      if (index === pathSegments.length - 1) {
        parent = current;
        lastKey = segment;
      } else if (current[segment] === undefined || current[segment] === null) {
        // Path doesn't exist in the custom config, nothing to reset
      } else {
        current = current[segment];
      }
    });

    // Remove the property from the custom config
    if (parent && lastKey) {
      logger.debug(`Removing customization at path: ${path}, key: ${lastKey}`);
      delete parent[lastKey];

      // Clean up empty objects
      let cleanupPath = pathSegments.slice(0, -1);
      while (cleanupPath.length > 0) {
        const tempObj = cleanupPath.reduce(
          (acc, segment) => (acc && acc[segment] ? acc[segment] : undefined),
          newCustomConfig,
        );

        // If object is empty, remove it
        if (tempObj && Object.keys(tempObj).length === 0) {
          const parentPath = cleanupPath.slice(0, -1);
          const lastSegment = cleanupPath[cleanupPath.length - 1];

          const parentObj = parentPath.reduce(
            (acc, segment) => (acc && acc[segment] ? acc[segment] : undefined),
            newCustomConfig,
          );

          if (parentObj) {
            delete parentObj[lastSegment];
            cleanupPath = parentPath;
          } else {
            break;
          }
        } else {
          break;
        }
      }

      // For debugging
      logger.debug('Custom config after reset:', JSON.stringify(newCustomConfig));

      // Update the custom configuration
      return updateConfiguration(newCustomConfig);
    }

    return false;
  };

  // Check if a value is customized or default
  const isCustomized = (path) => {
    if (!customConfig || !path) {
      return false;
    }

    try {
      // Split the path into segments, handling array indices properly
      const pathSegments = path.split(/[.[\]]+/).filter(Boolean);

      // Helper function to get value at path for comparison
      const getValueAtPath = (obj, segments) => {
        return segments.reduce((acc, segment) => {
          if (acc === null || acc === undefined || !Object.hasOwn(acc, segment)) {
            return undefined;
          }
          return acc[segment];
        }, obj);
      };

      // Get values from both custom and default configs
      const customValue = getValueAtPath(customConfig, pathSegments);
      const defaultValue = getValueAtPath(defaultConfig, pathSegments);

      // First check if the custom value exists
      const customValueExists = customValue !== undefined;

      // Special case for empty objects - they should count as not customized
      if (
        customValueExists &&
        typeof customValue === 'object' &&
        customValue !== null &&
        !Array.isArray(customValue) &&
        Object.keys(customValue).length === 0
      ) {
        return false;
      }

      // Special case for arrays
      if (customValueExists && Array.isArray(customValue)) {
        if (customValue.length === 0) return false; // Empty arrays aren't considered customized

        // Compare arrays for deep equality
        if (Array.isArray(defaultValue)) {
          // Different lengths means customized
          if (customValue.length !== defaultValue.length) return true;

          // Deep compare each element
          for (let i = 0; i < customValue.length; i += 1) {
            if (JSON.stringify(customValue[i]) !== JSON.stringify(defaultValue[i])) {
              return true;
            }
          }
          return false; // Arrays are identical
        }
        return true; // Custom is array, default isn't or is undefined
      }

      // Deep compare objects
      if (
        customValueExists &&
        typeof customValue === 'object' &&
        customValue !== null &&
        typeof defaultValue === 'object' &&
        defaultValue !== null
      ) {
        return JSON.stringify(customValue) !== JSON.stringify(defaultValue);
      }

      // Simple value comparison
      return customValueExists && customValue !== defaultValue;
    } catch (err) {
      logger.error(`Error in isCustomized for path: ${path}`, err);
      return false;
    }
  };

  useEffect(() => {
    fetchConfiguration();
  }, []);

  return {
    schema,
    defaultConfig,
    customConfig,
    mergedConfig,
    loading,
    error,
    fetchConfiguration,
    updateConfiguration,
    resetToDefault,
    isCustomized,
  };
};

export default useConfiguration;
