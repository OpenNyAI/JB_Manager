## GCP Deployment

**IMPORTANT**: The commands below are written for the Google Cloud SDK in a Linux environment. Please refer to the [Google Cloud SDK documentation](https://cloud.google.com/sdk/docs/install) for installation instructions.

### 1. Create a parameters file in the same directory as the script file, `gcp-deployment.yaml`. The parameters file should have the following structure:

```yaml
parameters:
  resourceNamePrefix: jb-test
  location: us-central1
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

### 2. Run the following command to deploy the template:

```
gcloud deployment-manager deployments create jugalbandi-deployment --config gcp-deployment.yaml

```