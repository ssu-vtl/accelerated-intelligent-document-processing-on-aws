// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

/* Maps call attributes from API to a format that can be used in tables and panel */
// eslint-disable-next-line arrow-body-style
const mapDocumentsAttributes = (documents) => {
  console.log('XXXXdocuments', documents);
  return documents.map((item) => {
    const {
      ObjectKey: objectKey,
      ObjectStatus: objectStatus,
      InitialEventTime: initialEventTime,
      QueuedTime: queuedTime,
      WorkflowStartTime: workflowStartTime,
      CompletionTime: completionTime,
      WorkflowExecutionArn: workflowExecutionArn,
      WorkflowStatus: workflowStatus,
      ListPK: listPK,
      ListSK: listSK,
    } = item;

    const mapping = {
      objectKey,
      objectStatus,
      initialEventTime: new Date(initialEventTime).toISOString(),
      queuedTime: new Date(queuedTime).toISOString(),
      workflowStartTime: new Date(workflowStartTime).toISOString(),
      completionTime: new Date(completionTime).toISOString(),
      workflowExecutionArn,
      workflowStatus,
      listPK,
      listSK,
    };

    console.log('XXXXdocument-mapping', mapping);

    return mapping;
  });
};

export default mapDocumentsAttributes;
