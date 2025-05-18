import json
import boto3

ENDPOINT = "huggingface-pytorch-tgi-inference-"

sagemaker_runtime = boto3.client("sagemaker-runtime", region_name='us-east-1')

def lambda_handler(event, context):
    query_params = event['queryStringParameters']
    query = query_params['query']
    payload = {
        "inputs": query,
        "parameters": {
            "max_new_tokens": 256,
            "top_p": 0.9,
            "temperature": 0.6,
            "top_k": 50,
            "repetion_penalty" : 1.03,
            "do_sample" : True
        }
    }
    response = sagemaker_runtime.invoke_endpoint(EndpointName=ENDPOINT,
                                                  ContentType="application/json",
                                                  Body=json.dumps(payload))
    predictions = json.loads(response['Body'].read().decode('utf-8'))
    final_result = predictions[0]['generated_text']
    return {
        'statusCode': 200,
        'body': json.dumps(final_result)
    }




##### LAMBDA API TEST ######

{
  "httpMethod" : "GET",
  "path" : "/example",
  "queryStringParameters" : {
    "query" : "Write an article on Computer Vision"
  }
}


#### BROWSER/POSTMAN API TEST ###
###  Example URL - > www.example_function_url.com/?query=What iS Deep Learning

#### Delete Every AWS Resource Created #####
#Delete Notebook Instance -> Model -> Model Endpoints