# CotacoesMoedas_emails
O codigo vai utilizado para automação de varios processos simultaneamente utilizando threads que vai otimizar o tempo.
1° parte- a função fetch_bcb_data vai usar uma api do banco central para resgatar a cotação de moedas, após isso vai ser utilizado o pandas para transformar isso em uma tabela
2° parte- Enquanto está ocorrendo a cotação das moedas a função generate_plot vai esperar 10 segundos até ter no minimo três moedas cotadas na tabela, após isso a função vai mesclar esses dados e vai gerar um gráfico, alertar a thread do email que o processo ta liberado e vai dar um valor a image_path.
3° parte - A função send_email vai validar se houver liberação de thread, e se a image_path possui algum valor que não seja none, liberado o processo a função projeto o dados que devem ser inseridos no email e dentro da função send_email tem a função send_ que vai usar o protocolo SMTP para enviar os emails usando threads de forma simutânea 
4° parte - A função main vai dar entrada com os dados necessarios e vai iniciar as threads.
