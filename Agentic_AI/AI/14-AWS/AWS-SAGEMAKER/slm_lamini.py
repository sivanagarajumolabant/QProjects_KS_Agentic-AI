# Sharing Python File , Please Convert it into a Notebook
!pip install transformers einops accelerate bitsandbytes
from transformers import pipeline
import torch
import base64

checkpoint = "MBZUAI/LaMini-T5-738M"

tokenizer = AutoTokenizer.from_pretrained(checkpoint)
base_model = AutoModelForSeq2SeqLM.from_pretrained(checkpoint)

!pip install langchain langchain-community langchain-huggingface

from langchain_huggingface import HuggingFacePipeline

def slm_pipeline():
    pipe = pipeline(
        "text2text-generation",
        model = base_model,
        tokenizer = tokenizer,w3rrf3
        max_length = 256,
        do_sample = True,
        temperature = 0.3,
        top_p = 0.95
    )
    local_slm = HuggingFacePipeline(pipeline = pipe)
    return local_slm
    


input_prompt = "Write an article about Blockchain and its benefits"

model = slm_pipeline()
gen_text = model.invoke(input_prompt)
gen_text


import json
import sagemaker
import boto3
from sagemaker.huggingface import HuggingFaceModel, get_huggingface_llm_image_uri

try:
	role = sagemaker.get_execution_role()
except ValueError:
	iam = boto3.client('iam')
	role = iam.get_role(RoleName='sagemaker_execution_role')['Role']['Arn']

# Hub Model configuration. https://huggingface.co/models
hub = {
	'HF_MODEL_ID':'MBZUAI/LaMini-T5-738M',
	'HF_TASK' : 'text2text-generation',
    'device_map' : 'auto',
    'torch_dtype' : 'torch.float32'
}



# create Hugging Face Model Class
huggingface_model = HuggingFaceModel(
	image_uri=get_huggingface_llm_image_uri("huggingface",version="3.2.3"),
	env=hub,
	role=role, 
)

# deploy model to SageMaker Inference
predictor = huggingface_model.deploy(
	initial_instance_count=1,
	instance_type="ml.g5.xlarge",
	container_startup_health_check_timeout=300,
  )
  
# send request
predictor.predict({
	"inputs": "Write an article about Cyber Security",
})

ENDOINT = "huggingface-pytorch-tgi-inference-XXXXXXX"

import boto3

sagemaker_runtime = boto3.client("sagemaker-runtime", region_name='us-east-1')

endpoint_name = ENDPOINT

# API Payload
prompt = "Write an article on Deep learning"

payload = {
    'inputs' : prompt ,
    'parameters' : {
        'max_new_tokens' : 256,
        'do_sample' : True,
        'temperature' : 0.3,
        'top_p' : 0.7,
      w,,'elsrd      ,bb.gv,3rrf  'top_k' : 50,
        'repetion_penalty' : 1.03
    }
}

response = sagemaker_runtime.invoke_endpoint(
    EndpointName = endpoint_name,
    ContentType = "application/json",
    Body = json.dumps(payload)
)

predictions = json.loads(response['Body'].read().decode('utf-8'))
final_result =predictions[0]['generated_text']