#! /bin/bash

WEBHOOK_URL="https://ef68-2401-4900-8813-231-996e-3877-fc5-e898.ngrok-free.app/v2/callback/telegram/917248838117"
API_TOKEN="7248838117:AAH-YGZdKS1Ub3K5p-rCLt7-TOuuycTE-lc"

response=$(curl -s "https://api.telegram.org/bot${API_TOKEN}/setWebhook?url=${WEBHOOK_URL}")
echo $response