import difflib

# Pre-defined mapping dictionary, defining corresponding mappings for different categories
STANDARD_MAPPING_SERVERLESS_PLATFORMS = {
    "AWS": "AWS Lambda",
    "Lambda": "AWS Lambda",
    "AWS SAM CLI": "AWS Lambda",
    "Amazon Alexa Skills Kit": "AWS Lambda",
    "AWS Lambda@Edge": "AWS Lambda",
    "Azure Functions": "Microsoft Azure",
    "AZ Functions": "Microsoft Azure",
    "Azure": "Microsoft Azure",
    "Azure Container Apps": "Microsoft Azure",
    "Azure Logic Apps": "Microsoft Azure",
    "Microsoft Azure Functions": "Microsoft Azure",
    "Apache OpenWhisk": "OpenWhisk",
    "Fn Project": "Fn",
    "Oracle Fn": "Fn",
    "Twilio runtime": "Twilio",
    "Twilio Functions": "Twilio",
    "Google Cloud": "Google Cloud Functions",
    "Google Cloud Function": "Google Cloud Functions",
    "Google Cloud Run": "Google Cloud Functions",
    "Google Cloud Platform (GCP)": "Google Cloud Functions",
    "GCP": "Google Cloud Functions",
    "Openwhisk": "OpenWhisk"
}

STANDARD_MAPPING_CLOUD_SERVICES = {
    # AWS
    "Amazon Aurora": "AWS Aurora",
    "Amazon Alexa Skills Kit": "AWS Alexa Skills Kit",
    "Alexa Skill": "AWS Alexa Skills Kit",
    "Alexa Skills Kit": "AWS Alexa Skills Kit",
    "Alexa": "AWS Alexa Skills Kit",
    "Alexa Skills Kit (ASK)": "AWS Alexa Skills Kit",
    "DynamoDB": "AWS DynamoDB",
    "AWS DynamoDB Streams": "AWS DynamoDB",
    "Amazon DynamoDB": "AWS DynamoDB",
    "API Gateway": "AWS API Gateway",
    "Amazon API Gateway": "AWS API Gateway",
    "AWS API Gateway (WebSocket)": "AWS API Gateway",
    "AWS ACM":"AWS Certificate Manager",
    "ACM":"AWS Certificate Manager",
    "CloudFormation": "AWS CloudFormation",
    "CloudFront": "AWS CloudFront",
    "Amazon CloudFront": "AWS CloudFront",
    "Cloudwatch": "AWS CloudWatch",
    "Amazon CloudWatch": "AWS CloudWatch",
    "Amazon CloudWatch Logs": "AWS CloudWatch",
    "AWS CloudWatch Events": "AWS CloudWatch",
    "Amazon Cognito": "AWS Cognito",
    "Amazon EC2": "AWS EC2",
    "Amazon EKS": "AWS EKS",
    "Amazon Elastic Load Balancing": "AWS Elastic Load Balancing",
    "Amazon Elastic Load Balancer": "AWS Elastic Load Balancing",
    "Elasticsearch": "AWS Elasticsearch",
    "AWS Elasticsearch Service": "AWS Elasticsearch",
    "Heroku Postgres": "AWS Heroku Postgres",
    "Amazon IAM": "AWS IAM",
    "AWS Lambda Invocation Service": "AWS Invocation Service",
    "IoT": "AWS IoT",
    "AWS IoT Core": "AWS IoT",
    "Amazon Inspector": "AWS Inspector",
    "Kinesis": "AWS Kinesis",
    "Amazon Kinesis": "AWS Kinesis",
    "Amazon Kinesis Analytics": "AWS Kinesis",
    "Amazon Kinesis Firehose": "AWS Kinesis",
    "AWS Kinesis Data Streams": "AWS Kinesis",
    "AWS Kinesis Data Stream": "AWS Kinesis",
    "AWS Key Management Service (KMS)": "AWS Key Management Service",
    "Amazon Lex": "AWS Lex",
    "AWS MongoDB": "MongoDB Atlas",
    "Amazon MSK (Managed Streaming for Apache Kafka)": "AWS MSK",
    "S3": "AWS S3",
    "Amazon S3": "AWS S3",
    "SES": "AWS SES",
    "Amazon SES": "AWS SES",
    "AWS Simple Email Service (SES)": "AWS SES",
    "AWS SES (Simple Email Service)": "AWS SES",
    "Amazon SES (Simple Email Service)": "AWS SES",
    "Amazon Simple Email Service": "AWS SES",
    "AWS Systems Manager Parameter Store": "AWS SSM",
    "Systems Manager Parameter Store": "AWS SSM",
    "Amazon SNS": "AWS SNS",
    "AWS SNS (Simple Notification Service)": "AWS SNS",
    "SQS": "AWS SQS",
    "Amazon SQS": "AWS SQS",
    "Security Token Service": "AWS STS",
    "AWS Security Token Service": "AWS STS",
    "Amazon RDS": "AWS RDS",
    "AWS Route53": "AWS Route 53",
    "Transcribe": "AWS Transcribe",
    "AWS Transcribe Service": "AWS Transcribe",
    "Amazon Rekognition": "AWS Rekognition",
    "Amazon VPC": "AWS VPC",
    # Azure
    "Azure App Service Plan": "Azure App Service",
    "Azure Web Apps": "Azure App Service",
    "Azure API Apps": "Azure App Service",
    "Azure Authorization Management": "Azure Authorization",
    "Azure AD": "Azure Active Directory",
    "Azure Active AD": "Azure Active Directory",
    "Microsoft Azure Active Directory (AAD)": "Azure Active Directory",
    "Azure Active Directory (AD)": "Azure Active Directory",
    "Azure Container Instance": "Azure Container Instances",
    "Azure Container Instances (ACI)": "Azure Container Instances",
    "Azure Cosmos DB": "Azure CosmosDB",
    "Azure CDN Profile": "Azure CDN",
    "CDN": "Azure CDN",
    "Azure Content Delivery Network": "Azure CDN",
    "DNS Private Zone": "Azure Private DNS Zone",
    "Azure Kubernetes Service (AKS)": "Azure Kubernetes Service",
    "Azure AKS": "Azure Kubernetes Service",
    "Kubernetes": "Azure Kubernetes Service",
    "AKS": "Azure Kubernetes Service",
    "Azure User Assigned Managed Identity": "Azure Managed Identity",
    "Azure Resource Groups": "Azure Resource Group",
    "Azure RoleBased Access Control (RBAC)": "Azure RoleBased Access Control",
    "Microsoft Azure RoleBased Access Control (RBAC)": "Azure RoleBased Access Control",
    "Azure RBAC": "Azure RoleBased Access Control",
    "Azure Resource Manager (ARM)": "Azure Resource Manager",
    "Azure SQL Database": "Azure SQL",
    "Azure SQL Server": "Azure SQL",
    "Azure Storage File": "Azure Storage",
    "Azure Storage Account": "Azure Storage",
    "Azure Blob Storage": "Azure Storage",
    "Azure Blob": "Azure Storage",
    "Azure Blob Container": "Azure Storage",
    "Azure Service Bus": "Azure Service Bus Queue",
    "Azure Public IP": "Azure Public IP Address",
    "Private Endpoint": "Azure Private Endpoint",
    "Azure Virtual Machine": "Azure Virtual Machines",
    "Azure Virtual Network Peering": "Azure Virtual Network",
    
    # Google
    "Google Cloud Compute Engine": "Google Compute Engine",
    "Google Container Registry (GCR)": "Google Container Registry",
    "Google Cloud Container Registry (GCR)": "Google Container Registry",
    "Google Cloud Container Registry": "Google Container Registry",
    "Google Cloud IAM": "Google IAM",
    "Google Cloud Networking": "Google Cloud Network",
    "Google Cloud Service Account": "Google Cloud Service Accounts",
    "Google Kubernetes Engine (GKE)": "Google Kubernetes Engine",
    "Google Maps Geocoding API": "Google Maps API",
    "Google Map API": "Google Maps API",
    "GCS": "Google Storage",
    "GC Storage": "Google Storage",
    "Google Cloud Pub/Sub": "Google Pub/Sub",
    "Google PubSub": "Google Pub/Sub",
    "Google Cloud PubSub": "Google Pub/Sub",
    "PubSub": "Google Pub/Sub",
    
    # 
    "Cloudant": "OpenWhisk Cloudant",
    "IBM Cloudant": "OpenWhisk Cloudant",
    "Minio": "MinIO",
    "MongoDB": "MongoDB Atlas",
    "Twilio API": "Twilio",
    "Twilio Voice": "Twilio",
    "Twilio Voice API": "Twilio",
    "Twilio VoiceResponse": "Twilio",
    "Twilio VoiceResponse API": "Twilio",
}

STANDARD_MAPPING_PROGRAMMING_LANGUAGES = {
    "Golang": "Go",
    "Go (Golang)": "Go",
    "py": "Python",
    "Python 2.7": "Python",
    "Javascript": "JavaScript",
    "JS": "JavaScript",
    "JavaScript (Node.js)": "JavaScript",
    "JavaScript (NodeJS)": "JavaScript",
    "Typescript": "JavaScript",
    "TypeScript": "JavaScript",
    "Node.js": "JavaScript",
    "NodeJS": "JavaScript",
    "NodeJS (JavaScript)": "JavaScript",
    "Node.js (JavaScript)": "JavaScript",
    "CSharp": "C#",
}

def standardize_value(value, mapping, delimiter=","):
    """
    Standardize the values based on the incoming mapping dictionary:
      - If directly matching the mapping dictionary, return the corresponding standard name;
      - Otherwise, use difflib for fuzzy matching. If the matching degree is higher than the threshold, return the standard name;
        Otherwise, return the original value (or record for manual confirmation).
    """
    # Construct a lowercase key mapping dictionary while maintaining the original format of standard names
    mapping_lower = {k.lower(): v for k, v in mapping.items()}
    def process(single_value):
        single_value_lower = single_value.lower()
        if single_value_lower in mapping_lower:
            return mapping_lower[single_value_lower]
        # best_matches = difflib.get_close_matches(single_value_lower, mapping_lower.keys(), n=1, cutoff=threshold)
        # if best_matches:
        #     return mapping_lower[best_matches[0]]
        # return "Undefined: " + single_value
        return single_value

    # Check if there is a delimiter, and if so, split it for processing
    if delimiter in value:
        # Split by delimiter, removing the leading and trailing blanks of each sub value
        values = [token.strip() for token in value.split(delimiter)]
        standardized_values = [process(token) for token in values]
        # De duplication: Maintain the original order and only retain the standardized result that appears first
        unique_values = []
        for v in standardized_values:
            if v not in unique_values:
                unique_values.append(v)
        return delimiter.join(unique_values)
    else:
        return process(value)

def standardize_category(value, category):
    """
    Standardize input values based on category, and the category parameter must be one of the following three:
      - "used_serverless_platforms"
      - "used_cloud_services"
      - "used_programming_languages"
    """
    if category == "used_serverless_platforms":
        mapping = STANDARD_MAPPING_SERVERLESS_PLATFORMS
    elif category == "used_cloud_services":
        mapping = STANDARD_MAPPING_CLOUD_SERVICES
    elif category == "used_programming_languages":
        mapping = STANDARD_MAPPING_PROGRAMMING_LANGUAGES
    else:
        raise ValueError(f"Undifined: {category}")
    
    return standardize_value(value, mapping)
