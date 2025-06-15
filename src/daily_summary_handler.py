import json
import os
import boto3
import asyncio  # 1. Importe a biblioteca asyncio

from core.supabase_client import create_supabase_client

SQS_QUEUE_URL = os.environ.get("SQS_QUEUE_URL")
sqs = boto3.client("sqs")  # Não precisa mais de configuração de endpoint


async def get_active_accounts_from_db():
    """
    Esta função permanece exatamente igual, pois já é assíncrona.
    """
    print("Buscando contas ativas no banco de dados...")
    supabase = await create_supabase_client()
    try:
        response = (
            await supabase.table("mail_accounts")
            .select("id, user_id, is_active")
            .eq("is_active", True)
            .execute()
        )
        active_accounts = response.data
        print(f"Encontradas {len(active_accounts)} contas ativas.")
        return active_accounts
    except Exception as e:
        print(f"Erro ao buscar contas ativas: {e}")
        raise e


async def main_logic(event, context):
    """
    2. Toda a sua lógica principal foi movida para esta função async.
    """
    if not SQS_QUEUE_URL:
        raise EnvironmentError(
            "A variável de ambiente SQS_QUEUE_URL não está definida."
        )

    active_accounts = await get_active_accounts_from_db()

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

    for account in active_accounts:
        account_id = account.get("id")
        if not account_id:
            print(f"Pulando registro por falta de accountId: {account}")
            failure_count += 1
            continue
        try:
            message_body = json.dumps({"accountId": account_id})
            # (Veja a nota sobre o Boto3 abaixo)
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


def lambda_handler(event, context):
    """
    3. Este é o novo handler síncrono que a AWS Lambda vai chamar.
       Ele atua como uma "ponte" para o nosso código assíncrono.
    """
    # A mágica está aqui: asyncio.run() executa a nossa função async
    # e espera ela terminar, retornando o resultado.
    return asyncio.run(main_logic(event, context))
