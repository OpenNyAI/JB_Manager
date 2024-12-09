##AWS Deployment


**IMPORTANT**: The commands below are written for the AWS CLI in a Linux environment. Please refer to the [AWS CLI documentation] (https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html) for installation instructions.


###1. Create a parameters file in the same directory as the script file, `aws-deployment.yaml`. The parameters file should have the following structure:

```yaml
parameters:
  resourceNamePrefix: jb-test
  location: us-east-1
  postgresAdminUser: postgres
  postgresAdminPassword: postgres
  postgresDatabaseName: jb_db
  cpu: 0.5
  memory: 1Gi
  minReplicas: 1
  maxReplicas: 2
  bhashniApiKey: xxx
  bhashniPipelineID: xxx
  bhashniUserID: xxx
  encryptionKey: xxx
  whatsappAPIHost: https://example.com
  whatsappAPIKey: xxx
```

## 2. Run the following command to deploy the stack using CloudFormation:
```bash
aws cloudformation create-stack --stack-name jugalbandi-stack --template-body file://aws-deployment.yaml --parameters file://aws-parameters.yaml
```