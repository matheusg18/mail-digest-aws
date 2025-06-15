import json
import os
import boto3
from dotenv import load_dotenv

load_dotenv()

# Verifica se estamos em ambiente local
IS_LOCAL = os.environ.get("AWS_SAM_LOCAL") == "true"

# Configurações do SQS
SQS_QUEUE_URL = os.environ.get("SQS_QUEUE_URL")
sqs_client_config = {}

if IS_LOCAL:
    # Se for local, aponta para o LocalStack
    # Use a URL que você obteve no passo 2
    SQS_QUEUE_URL = "http://localhost:4566/000000000000/MailDigest-SummaryJobQueue"
    sqs_client_config["endpoint_url"] = "http://localhost:4566"

sqs = boto3.client("sqs", **sqs_client_config)


def get_active_accounts_from_db():
    """
    Função de exemplo para simular a busca de IDs de contas ativas do Supabase.
    Aqui você deve conectar ao seu banco de dados real.
    """
    print("Buscando contas ativas no banco de dados...")
    # Exemplo: Substitua isso pela sua consulta real ao banco de dados
    return [
        {"accountId": "uuid-da-conta-123"},
        {"accountId": "uuid-da-conta-456"},
        {"accountId": "uuid-da-conta-789"},
    ]


def lambda_handler(event, context):
    """
    Esta função é o "Dispatcher". Ela é acionada por um agendamento, busca todas
    as contas ativas do banco de dados e envia uma mensagem para uma fila SQS
    para que cada conta seja processada individualmente.
    """
    if not SQS_QUEUE_URL:
        raise EnvironmentError(
            "A variável de ambiente SQS_QUEUE_URL não está definida."
        )

    # 1. Busca todas as contas ativas do seu banco de dados (Supabase)
    active_accounts = get_active_accounts_from_db()

    if not active_accounts:
        print("Nenhuma conta ativa encontrada para processar.")
        return {
            "statusCode": 200,
            "body": json.dumps({"message": "Nenhuma conta ativa para processar."}),
        }

    print(
        f"Encontradas {len(active_accounts)} contas para processar. Enviando para a fila SQS..."
    )

    success_count = 0
    failure_count = 0

    # 2. Itera sobre as contas e envia uma mensagem para a SQS para cada uma
    for account in active_accounts:
        account_id = account.get("accountId")
        if not account_id:
            print(f"Pulando registro por falta de accountId: {account}")
            failure_count += 1
            continue

        try:
            message_body = json.dumps({"accountId": account_id})
            sqs.send_message(QueueUrl=SQS_QUEUE_URL, MessageBody=message_body)
            print(f"Mensagem enviada com sucesso para a conta: {account_id}")
            success_count += 1
        except Exception as e:
            print(f"Erro ao enviar mensagem para a conta {account_id}: {e}")
            failure_count += 1

    print(f"Despacho concluído. Sucessos: {success_count}, Falhas: {failure_count}")

    return {
        "statusCode": 200,
        "body": json.dumps(
            {
                "message": "Processo de despacho concluído.",
                "despachos_bem_sucedidos": success_count,
                "despachos_com_falha": failure_count,
            }
        ),
    }
