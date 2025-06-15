import json


def process_single_account(account_id):
    """
    É aqui que o trabalho pesado para uma única conta acontece.

    - Busca as credenciais do banco usando o account_id.
    - Conecta-se ao serviço de e-mail (ex: Gmail).
    - Busca os e-mails.
    - Obtém um resumo de um modelo de linguagem (ex: OpenAI).
    - Formata o resumo.
    - Envia o resumo via Telegram.
    """
    print(f"Iniciando processamento da conta com ID: {account_id}")

    # Simulação da sua implementação real
    try:
        # 1. Busca detalhes da conta no BD
        print(f"   - Buscando credenciais para {account_id} no Supabase...")

        # 2. Conecta ao Gmail
        print(f"   - Conectando ao serviço de e-mail para {account_id}...")

        # 3. Chama a OpenAI
        print(f"   - Gerando resumo com OpenAI para {account_id}...")

        # 4. Envia via Telegram
        print(f"   - Enviando resumo via Telegram para {account_id}...")

        print(f"Conta processada com sucesso: {account_id}")
        return True
    except Exception as e:
        print(f"Falha ao processar a conta {account_id}. Erro: {e}")
        # A exceção fará com que a SQS tente reenviar a mensagem
        raise e


def lambda_handler(event, context):
    """
    Esta função é o "Worker". Ela é acionada por uma ou mais mensagens
    da fila SQS. Cada mensagem contém o ID de uma conta que precisa
    ter seu resumo de e-mail processado.
    """
    print("Função Worker acionada.")
    print(f"Evento recebido: {json.dumps(event)}")

    # Eventos da SQS contêm uma lista de 'Records'
    for record in event.get("Records", []):
        try:
            # O corpo da mensagem é uma string JSON, então precisamos parseá-la
            message_body = json.loads(record.get("body", "{}"))
            account_id = message_body.get("accountId")

            if not account_id:
                print("Pulando registro por falta de 'accountId' no corpo da mensagem.")
                continue

            # Processa esta única conta
            process_single_account(account_id)

        except json.JSONDecodeError as e:
            print(
                f"Erro ao decodificar JSON do corpo da mensagem SQS: {record.get('body')}. Erro: {e}"
            )
        except Exception as e:
            print(f"Ocorreu um erro inesperado ao processar um registro: {e}")
            # Re-lançar a exceção é importante. Sinaliza para a Lambda e a SQS
            # que o processamento desta mensagem falhou e deve ser tentado novamente ou enviado para a DLQ.
            raise e

    return {"statusCode": 200, "body": json.dumps("Processamento concluído.")}
