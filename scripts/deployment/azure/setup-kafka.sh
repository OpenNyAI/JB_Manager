#!/bin/bash

# set-up EventHub with KAFKA endpoint
# create standard eventhub namespace

if [ $# -lt 3 ]; then
    echo "Usage: $0 resource_group Preferred_region Identifier"
    exit 1
fi

export RESOURCE_GROUP=$1
export PREFERRED_REGION=$2
export IDENTIFIER=$3

export EVENTHUB_NAMESPACE=ehnsjb-manager$IDENTIFIER
export EVENTHUB_SEND_POLICY=ehspjb-manager$IDENTIFIER
export EVENTHUB_LISTEN_POLICY=ehlpjb-manager$IDENTIFIER


az eventhubs namespace create --name $EVENTHUB_NAMESPACE \
--resource-group $RESOURCE_GROUP \
--location $PREFERRED_REGION \
--sku Standard \
--capacity 1 \
--enable-auto-inflate true \
--maximum-throughput-units 10 \
--enable-kafka true \
--zone-redundant false

# create a standard 4 eventhub / topic with 1 partition each

# FLOW
az eventhubs eventhub create --name $KAFKA_FLOW_TOPIC \
--namespace-name $EVENTHUB_NAMESPACE \
--resource-group $RESOURCE_GROUP \
--retention-time 1 \
--partition-count 1 \
--enable-capture false \
--cleanup-policy Delete \
--status Active

# CHANNEL
az eventhubs eventhub create --name $KAFKA_CHANNEL_TOPIC \
--namespace-name $EVENTHUB_NAMESPACE \
--resource-group $RESOURCE_GROUP \
--retention-time 1 \
--partition-count 1 \
--enable-capture false \
--cleanup-policy Delete \
--status Active

# LANGUAGE
az eventhubs eventhub create --name $KAFKA_LANGUAGE_TOPIC \
--namespace-name $EVENTHUB_NAMESPACE \
--resource-group $RESOURCE_GROUP \
--retention-time 1 \
--partition-count 1 \
--enable-capture false \
--cleanup-policy Delete \
--status Active

# LOGGER
az eventhubs eventhub create --name $KAFKA_LOGGER_TOPIC \
--namespace-name $EVENTHUB_NAMESPACE \
--resource-group $RESOURCE_GROUP \
--retention-time 1 \
--partition-count 1 \
--enable-capture false \
--cleanup-policy Delete \
--status Active

# create a shared policy one each for send and listen
az eventhubs namespace authorization-rule create --name $EVENTHUB_SEND_POLICY \
--namespace-name $EVENTHUB_NAMESPACE \
--resource-group $RESOURCE_GROUP \
--rights Send


az eventhubs namespace authorization-rule create --name $EVENTHUB_LISTEN_POLICY \
--namespace-name $EVENTHUB_NAMESPACE \
--resource-group $RESOURCE_GROUP \
--rights Listen


# show the eventhub connection string for both send and listen
KAFKA_PRODUCER_PASSWORD=$(az eventhubs namespace authorization-rule keys list --name $EVENTHUB_SEND_POLICY \
--namespace-name $EVENTHUB_NAMESPACE \
--resource-group $RESOURCE_GROUP \
--query "primaryConnectionString")

KAFKA_CONSUMER_PASSWORD=$(az eventhubs namespace authorization-rule keys list --name $EVENTHUB_LISTEN_POLICY \
--namespace-name $EVENTHUB_NAMESPACE \
--resource-group $RESOURCE_GROUP \
--query "primaryConnectionString")

export KAFKA_BROKER=$EVENTHUB_NAMESPACE.servicebus.windows.net:9093
export KAFKA_PRODUCER_USERNAME='$ConnectionString'
export KAFKA_PRODUCER_PASSWORD=$KAFKA_PRODUCER_PASSWORD
export KAFKA_CONSUMER_USERNAME='$ConnectionString'
export KAFKA_CONSUMER_PASSWORD=$KAFKA_CONSUMER_PASSWORD