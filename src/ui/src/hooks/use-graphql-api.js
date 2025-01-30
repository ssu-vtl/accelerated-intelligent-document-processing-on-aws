// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0
import { useEffect, useState } from 'react';
import { API, Logger, graphqlOperation } from 'aws-amplify';

import useAppContext from '../contexts/app';

import listDocumentsDateShard from '../graphql/queries/listDocumentsDateShard';
import listDocumentsDateHour from '../graphql/queries/listDocumentsDateHour';
import listDocuments from '../graphql/queries/listDocuments';
import getDocument from '../graphql/queries/getDocument';

import onCreateCall from '../graphql/queries/onCreateCall';
import onUpdateCall from '../graphql/queries/onUpdateCall';
import onDeleteCall from '../graphql/queries/onDeleteCall';
import onUnshareCall from '../graphql/queries/onUnshareCall';

import { DOCUMENT_LIST_SHARDS_PER_DAY } from '../components/document-list/documents-table-config';

const logger = new Logger('useGraphQlApi');

const useGraphQlApi = ({ initialPeriodsToLoad = DOCUMENT_LIST_SHARDS_PER_DAY * 2 } = {}) => {
  const [periodsToLoad, setPeriodsToLoad] = useState(initialPeriodsToLoad);
  const [isDocumentsListLoading, setIsDocumentsListLoading] = useState(false);
  const [calls, setCalls] = useState([]);
  const { setErrorMessage } = useAppContext();

  const setCallsDeduped = (documentValues) => {
    setCalls((currentCalls) => {
      const documentValuesdocumentIds = documentValues.map((c) => c.CallId);
      return [
        ...currentCalls.filter((c) => !documentValuesdocumentIds.includes(c.CallId)),
        ...documentValues.map((call) => ({
          ...call,
          ListPK: call.ListPK || currentCalls.find((c) => c.CallId === call.CallId)?.ListPK,
          ListSK: call.ListSK || currentCalls.find((c) => c.CallId === call.CallId)?.ListSK,
        })),
      ];
    });
  };

  const getDocumentDetailsFromIds = async (documentIds) => {
    // prettier-ignore
    logger.debug('getDocumentDetailsFromIds', documentIds);
    const getDocumentPromises = documentIds.map((id) => API.graphql({ query: getDocument, variables: { id } }));
    const getDocumentResolutions = await Promise.allSettled(getDocumentPromises);
    const getCallRejected = getDocumentResolutions.filter((r) => r.status === 'rejected');
    if (getCallRejected.length) {
      setErrorMessage('failed to get document details - please try again later');
      logger.error('get document promises rejected', getCallRejected);
    }
    const documentValues = getDocumentResolutions
      .filter((r) => r.status === 'fulfilled')
      .map((r) => r.value?.data?.getCall);

    return documentValues;
  };

  useEffect(() => {
    logger.debug('onCreateCall subscription');
    const subscription = API.graphql(graphqlOperation(onCreateCall)).subscribe({
      next: async ({ provider, value }) => {
        logger.debug('call list subscription update', { provider, value });
        const callId = value?.data?.onCreateCall.CallId || '';
        if (callId) {
          const documentValues = await getDocumentDetailsFromIds([callId]);
          setCallsDeduped(documentValues);
        }
      },
      error: (error) => {
        logger.error(error);
        setErrorMessage('call list network subscription failed - please reload the page');
      },
    });

    return () => subscription.unsubscribe();
  }, []);

  useEffect(() => {
    logger.debug('onUpdateCall subscription');
    const subscription = API.graphql(graphqlOperation(onUpdateCall)).subscribe({
      next: async ({ provider, value }) => {
        logger.debug('call update', { provider, value });
        const callUpdateEvent = value?.data?.onUpdateCall;
        if (callUpdateEvent?.CallId) {
          setCallsDeduped([callUpdateEvent]);
        }
      },
      error: (error) => {
        logger.error(error);
        setErrorMessage('call update network request failed - please reload the page');
      },
    });

    return () => subscription.unsubscribe();
  }, []);

  useEffect(() => {
    logger.debug('onDeleteCall subscription');
    const subscription = API.graphql(graphqlOperation(onDeleteCall)).subscribe({
      next: async ({ provider, value }) => {
        logger.debug('call delete subscription update', { provider, value });
        const callId = value?.data?.onDeleteCall.CallId || '';
        if (callId) {
          setCalls((currentCalls) => currentCalls.filter((c) => c.CallId !== callId));
        }
      },
      error: (error) => {
        logger.error(error);
        setErrorMessage('call delete subscription failed - please reload the page');
      },
    });

    return () => subscription.unsubscribe();
  }, []);

  useEffect(() => {
    logger.debug('onUnshareCall subscription');
    const subscription = API.graphql(graphqlOperation(onUnshareCall)).subscribe({
      next: async ({ provider, value }) => {
        logger.debug('call unshare subscription update', { provider, value });
        const callId = value?.data?.onUnshareCall.CallId || '';
        if (callId) {
          setCalls((currentCalls) => currentCalls.filter((c) => c.CallId !== callId));
        }
      },
      error: (error) => {
        logger.error(error);
        setErrorMessage('call delete subscription failed - please reload the page');
      },
    });

    return () => subscription.unsubscribe();
  }, []);

  const listDocumentIdsByDateShards = async ({ date, shards }) => {
    const listDocumentsDateShardPromises = shards.map((i) => {
      logger.debug('sending list document date shard', date, i);
      return API.graphql({ query: listDocumentsDateShard, variables: { date, shard: i } });
    });
    const listDocumentsDateShardResolutions = await Promise.allSettled(listDocumentsDateShardPromises);

    const listRejected = listDocumentsDateShardResolutions.filter((r) => r.status === 'rejected');
    if (listRejected.length) {
      setErrorMessage('failed to list documents - please try again later');
      logger.error('list document promises rejected', listRejected);
    }
    const documentData = listDocumentsDateShardResolutions
      .filter((r) => r.status === 'fulfilled')
      .map((r) => r.value?.data?.listDocumentsDateShard?.Documents || [])
      .reduce((pv, cv) => [...cv, ...pv], []);

    return documentData;
  };

  const listDocumentIdsByDateHours = async ({ date, hours }) => {
    const listDocumentsDateHourPromises = hours.map((i) => {
      logger.debug('sending list document date hour', date, i);
      return API.graphql({ query: listDocumentsDateHour, variables: { date, hour: i } });
    });
    const listDocumentsDateHourResolutions = await Promise.allSettled(listDocumentsDateHourPromises);

    const listRejected = listDocumentsDateHourResolutions.filter((r) => r.status === 'rejected');
    if (listRejected.length) {
      setErrorMessage('failed to list documents - please try again later');
      logger.error('list document promises rejected', listRejected);
    }

    const documentData = listDocumentsDateHourResolutions
      .filter((r) => r.status === 'fulfilled')
      .map((r) => r.value?.data?.listDocumentsDateHour?.Documents || [])
      .reduce((pv, cv) => [...cv, ...pv], []);

    return documentData;
  };

  // eslint-disable-next-line no-unused-vars
  const listdocumentIds = async () => {
    // this uses a Scan of dynamoDB - prefer using the shard based queries
    const listDocumentsPromise = API.graphql({ query: listDocuments });
    const listDocumentsResolutions = await Promise.allSettled([listDocumentsPromise]);

    const listRejected = listDocumentsResolutions.filter((r) => r.status === 'rejected');
    if (listRejected.length) {
      setErrorMessage('failed to list Documents - please try again later');
      logger.error('list call promises rejected', listRejected);
    }

    const documentIds = listDocumentsResolutions
      .filter((r) => r.status === 'fulfilled')
      .map((r) => r.value?.data?.listDocuments?.Documents || [])
      .map((items) => items.map((item) => item?.CallId))
      .reduce((pv, cv) => [...cv, ...pv], []);

    return documentIds;
  };

  const sendSetDocumentsForPeriod = async () => {
    // XXX this logic should be moved to the API
    try {
      const now = new Date();

      // array of arrays containing date / shard pairs relative to current UTC time
      // e.g. 2 periods to on load 2021-01-01T:20:00:00.000Z ->
      // [ [ '2021-01-01', 3 ], [ '2021-01-01', 4 ] ]
      const hoursInShard = 24 / DOCUMENT_LIST_SHARDS_PER_DAY;
      const dateShardPairs = [...Array(parseInt(periodsToLoad, 10)).keys()].map((p) => {
        const deltaInHours = p * hoursInShard;
        const relativeDate = new Date(now - deltaInHours * 3600 * 1000);

        const relativeDateString = relativeDate.toISOString().split('T')[0];
        const shard = Math.floor(relativeDate.getUTCHours() / hoursInShard);

        return [relativeDateString, shard];
      });

      // reduce array of date/shard pairs into object of shards by date
      // e.g. [ [ '2021-01-01', 3 ], [ '2021-01-01', 4 ] ] -> { '2021-01-01': [ 3, 4 ] }
      const dateShards = dateShardPairs.reduce((p, c) => ({ ...p, [c[0]]: [...(p[c[0]] || []), c[1]] }), {});
      logger.debug('document list date shards', dateShards);

      // parallelizes listDocuments and getDocumentDetails
      // alternatively we could implement it by sending multiple graphql queries in 1 request
      const documentDataDateShardPromises = Object.keys(dateShards).map(
        // pretttier-ignore
        async (d) => listDocumentIdsByDateShards({ date: d, shards: dateShards[d] }),
      );

      // get contact Ids by hour on residual hours outside of the lower shard date/hour boundary
      // or just last n hours when periodsToLoad is less than 1 shard period
      let baseDate;
      let residualHours;
      if (periodsToLoad < 1) {
        baseDate = new Date(now);
        const numHours = parseInt(periodsToLoad * hoursInShard, 10);
        residualHours = [...Array(numHours).keys()].map((h) => baseDate.getUTCHours() - h);
      } else {
        baseDate = new Date(now - periodsToLoad * hoursInShard * 3600 * 1000);
        const residualBaseHour = baseDate.getUTCHours() % hoursInShard;
        residualHours = [...Array(hoursInShard - residualBaseHour).keys()].map((h) => baseDate.getUTCHours() + h);
      }
      const baseDateString = baseDate.toISOString().split('T')[0];

      const residualDateHours = { date: baseDateString, hours: residualHours };
      logger.debug('document list date hours', residualDateHours);

      const documentDataDateHourPromise = listDocumentIdsByDateHours(residualDateHours);

      const documentDataPromises = [...documentDataDateShardPromises, documentDataDateHourPromise];
      const documentDetailsPromises = documentDataPromises.map(async (documentDataPromise) => {
        const documentData = await documentDataPromise;
        const documentIds = documentData.map((item) => item.object_key);
        const documentDetails = await getDocumentDetailsFromIds(documentIds);
        // Merge document details with PK and SK
        return documentDetails.map((detail) => {
          const matchingData = documentData.find((item) => item.object_key === detail.object_key);
          return { ...detail, ListPK: matchingData.PK, ListSK: matchingData.SK };
        });
      });

      const documentValuesPromises = documentDetailsPromises.map(async (documentValuesPromise) => {
        const documentValues = await documentValuesPromise;
        logger.debug('documentValues', documentValues);
        return documentValues;
      });

      const getDocumentsPromiseResolutions = await Promise.allSettled(documentValuesPromises);
      logger.debug('getDocumentsPromiseResolutions', getDocumentsPromiseResolutions);
      const documentValuesReduced = getDocumentsPromiseResolutions
        .filter((r) => r.status === 'fulfilled')
        .map((r) => r.value)
        .reduce((previous, current) => [...previous, ...current], []);
      logger.debug('documentValuesReduced', documentValuesReduced);
      setCallsDeduped(documentValuesReduced);
      setIsDocumentsListLoading(false);
      const getCallsRejected = getDocumentsPromiseResolutions.filter((r) => r.status === 'rejected');
      if (getCallsRejected.length) {
        setErrorMessage('failed to get call details - please try again later');
        logger.error('get call promises rejected', getCallsRejected);
      }
    } catch (error) {
      setIsDocumentsListLoading(false);
      setErrorMessage('failed to list Documents - please try again later');
      logger.error('error obtaining call list', error);
    }
  };

  useEffect(() => {
    if (isDocumentsListLoading) {
      logger.debug('call list is loading');
      // send in a timeout to avoid blocking rendering
      setTimeout(() => {
        setCalls([]);
        sendSetDocumentsForPeriod();
      }, 1);
    }
  }, [isDocumentsListLoading]);

  useEffect(() => {
    logger.debug('list period changed', periodsToLoad);
    setIsDocumentsListLoading(true);
  }, [periodsToLoad]);

  return {
    calls,
    isDocumentsListLoading,
    getDocumentDetailsFromIds,
    setIsDocumentsListLoading,
    setPeriodsToLoad,
    periodsToLoad,
  };
};

export default useGraphQlApi;
