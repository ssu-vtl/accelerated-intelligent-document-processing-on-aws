import boto3
import json
import argparse

def parse_arguments():
    parser = argparse.ArgumentParser(description='Make predictions using a SageMaker endpoint')
    parser.add_argument('--endpoint-name', 
                       type=str, 
                       required=True,
                       help='Name of the SageMaker endpoint')
    parser.add_argument('--region', 
                       type=str, 
                       default='us-west-2',
                       help='AWS region (default: us-west-2)')
    return parser.parse_args()

def predict_from_endpoint(endpoint_name, input_payload, region):
    """
    Sends a request to the SageMaker endpoint for prediction.
    :param endpoint_name: Name of the deployed SageMaker endpoint
    :param input_payload: Input data for prediction
    :param region: AWS region
    :return: Prediction result from the endpoint
    """
    # Initialize SageMaker runtime client
    sagemaker_runtime = boto3.client("sagemaker-runtime", region_name=region)

    # Convert to JSON string
    input_data = json.dumps(input_payload)

    # Invoke the endpoint
    response = sagemaker_runtime.invoke_endpoint(
        EndpointName=endpoint_name,
        Body=input_data,
        ContentType="application/json"
    )
    print(response)
    
    # Parse the response
    result = response["Body"].read().decode("utf-8")
    print("Response body:", result)

    return json.loads(result)

def main():
    # Parse command line arguments
    args = parse_arguments()

    # testing sample from s3
    json_path = "s3://idp-udop-workingbucket-qhjtiezlji94/insurance-bundle.pdf/textract_document_text_raw/page_0001.json"
    image_path = "s3://idp-udop-workingbucket-qhjtiezlji94/insurance-bundle.pdf/images/page_0001.jpg"

    # Prepare input
    inputs = {"image": image_path, "textract": json_path}
    print(f"Input: {inputs}")

    # Get prediction
    prediction = predict_from_endpoint(args.endpoint_name, inputs, args.region)
    print("Prediction result:", prediction['prediction'])

if __name__ == "__main__":
    main()