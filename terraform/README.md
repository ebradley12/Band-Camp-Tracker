# **Terraform Folder README**

---

## **Overview**

This folder contains the Terraform scripts that define the complete infrastructure for the Band Camp Tracker project. The infrastructure is designed to collect data from the BandCamp website and API, process it through an ETL pipeline, store it in a database, generate PDF reports, send alerts based on trending and popular music genres and provide a dashboard for users to interact with and visualize the data.
The key components defined in the Terraform folder are AWS lambda functions for the  ETL pipeline, report generation which uses EventBridge and SES to send daily reports, the dashboard which is hosted on AWS Fargate and utilises a Load Balancer for scalability, alerts which utilise AWS lambda which triggers via EventBridge once per hour, Amazon RDS, Amazon S3, Amazon ECR and AWS security features.
### Design Philosophy:
- **Efficiency**: Serverless technologies like Lambda and managed services like RDS reduce operational overhead.
- **Scalability**: Resources such as Fargate, S3, and ALB are highly scalable to handle varying workloads.
- **Maintainability**: Modular Terraform scripts allow independent management of different components, enabling easier updates and deployment.

---

## **Contents**

### **File Structure**
The terraform files are organised based on their function. The overall file structure can be seen below.
```
terraform/ 
    ├── dashboard/ 
    ├── ecr/  
    ├── alerts/
    ├── pipeline/
    ├── rds/
    ├── reports/
    ├── provider.tf
    ├── variables.tf
```

### **Scripts**
1. **`pipeline.tf`**
    - Configure IAM roles and policies to grant permissions for Lambda and other AWS services.
    - Define the Lambda function for the ETL pipeline and schedules it to run every 10 minutes.
    - Manages the docker image for the Lambda function, including lifecycle policies to optimise storage.

2. **`provider.tf`**
    - Configures the AWS provider to use the `eu-west-2` region for resource deployment.
    - Specifies the required AWS provider version for compatibility and stability.

3. **`rds.tf`**
    - Configures the ingress and egress rules to allow traffic on PostgreSQL port 5432.
    - Provisions a PostgreSQL database with `db.t3.micro` instance type, automated backups, and performance insights enabled.
    - Associates the database with the specified security group and makes it publicly available for connectivity.

4. **`report.tf`**
    - Creates an S3 bucket to store PDF reports with production environment tagging.
    - Defines a lambda function for report generation, with IAM roles and policies granting access to S3, SES, RDS and CloudWatch.
    - Schedules the lambda function to run daily and 9am via EventBridge.

5. **`variables.tf`**
    - Defines sensitive variables for database connection, including username, password, name, host, and port.
    - Specifies the S3 bucket name for report storage and SES email addresses for sending and receiving reports.
    - Ensures secure handling of sensitive data with defaults where applicable, like the database port.

6. **`dashboard.tf`**
    - Application Load Balancer (ALB) for routing traffic.
    - ECS service for running the dashboard application.
    - Security groups and IAM roles specific to the dashboard.

7. **`alerts.tf`**
    ...

---

## **How to Run the Terraform Scripts**

### **Prerequisites**
- Terraform 1.5 or later installed.
- AWS CLI installed and configured with appropriate credentials.
- The `.tfvars` file in the root directory containing the necessary variable values:
    ```
    db_user = "<Your RDS Username>"
    db_password = "<Your RDS Password>"
    db_name = "<Your Database Name>"
    db_host = "<Your RDS Endpoint>"
    s3_bucket_name = "<Your S3 Bucket Name>"
    sender_email = "<Your SES Sender Email>"
    recipient_email = "<Your SES Recipient Email>"
    ```

### **Provisioning ECRs and Configuring Components**
Before proceeding with the deployment, ensure that Elastic Container Registries (ECRs) are provisioned, using the steps below. This step is necessary as each component’s deployment depends on pre-provisioned ECRs. Once the ECRs are ready, navigate to the respective subfolder within the Terraform directory and use the same process to configure and apply the deployment for each component individually.

# **Steps**

1. **Initialise Terraform**
Navigate to the desired folder within the terraform folder.
Prepare the working directory and download provider plugins:
```
terraform init
```

2. **Validate the Configuration:**
Ensure the Terraform files are correctly configured:
```
terraform validate
```

3. **Plan the Deployment:**
Generate an execution plan to preview the infrastructure changes:
```
terraform plan
```

4. **Apply the Configuration:**
Deploy the infrastructure to your AWS account:
```
terraform apply
```

5. **Destroy the Infrastructure (if needed):**
Tear down the deployed resources:
```
terraform destroy
```