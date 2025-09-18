#!/bin/bash
echo "Starting the Cloud Build process..."
gcloud builds submit --config cloudbuild.yaml .
echo "Cloud Build process finished."
