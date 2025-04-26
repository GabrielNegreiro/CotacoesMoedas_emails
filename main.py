import threading
import requests
import pandas as pd
import matplotlib
matplotlib.use('Agg') 
import matplotlib.pyplot as plt
import smtplib #SMTP (Simple Mail Transfer Protocol) 
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage

# Configurações
EMAIL_FROM = "Coloque seu email aqui"
EMAIL_TO = []#os emails que vc quer enviar
EMAIL_PASSWORD = "" #sua senha de app do gmail
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
# Variáveis compartilhadas
resultados = {}
plot_ready = threading.Condition()
image_path = None

def fetch_bcb_data(codigo, nome):
    print(f"🔍 Buscando dados para: {nome}")
    try:
        url = f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.{codigo}/dados/ultimos/20?formato=json"
        response = requests.get(url).json()
        df = pd.DataFrame(response)
        df["data"] = pd.to_datetime(df["data"], dayfirst=True)
        df["valor"] = pd.to_numeric(df["valor"])
        df.rename(columns={"valor": nome}, inplace=True)
        
        with plot_ready:
            resultados[nome] = df.set_index("data")
        print(f"✅ Dados recebidos: {nome}")
    except Exception as e:
        print(f"❌ Erro ao buscar {nome}: {e}")

def generate_plot():
    global image_path
    print("📊 Aguardando todos os dados para gerar o gráfico...")

    timeout = time.time() + 10  # espera até 10 segundos
    while len(resultados) < 3 and time.time() < timeout:
        time.sleep(0.2)

    if len(resultados) < 3:
        with plot_ready:
            plot_ready.notify_all()  # Notifica o e-mail mesmo que falhe, evitando deadlock

        print("⚠️ Timeout esperando os dados. Dados incompletos:", resultados.keys())
        return

    #dados = pd.concat([resultados["Dólar (R$)"], resultados["Euro (R$)"], resultados["Ouro (R$/g)"]], axis=1)
    dados = pd.concat(resultados.values(), axis=1)

    #cria uma figura do grafico
    plt.figure(figsize=(12, 6))
    #tema do grafico
    plt.style.use("seaborn-v0_8-darkgrid")

    #dados.index: são as datas.
    #dados[coluna]: são os valores (as cotações).
    #marker="o": coloca bolinhas nos pontos dos dados.
    #linestyle="-": conecta os pontos com uma linha.
    #label=coluna: dá o nome da moeda na legenda do gráfico.
    
    for coluna in dados.columns:
        plt.plot(dados.index, dados[coluna], marker="o", linestyle="-", label=coluna)
    plt.title("Cotações (Últimos 20 Dias)")
    plt.legend()
    #ajusta o grafico para ter sobreposição de elementos
    plt.tight_layout()

    image_path = "cotacoes.png"
    plt.savefig(image_path, dpi=300)
    plt.close()
    print(f"✅ Gráfico gerado: {image_path}")

    with plot_ready:
        plot_ready.notify_all()

def send_email():
    global image_path
    start_time = time.time()
    print("📧 Aguardando gráfico para envio de e-mail...")

    with plot_ready:
        waited = plot_ready.wait(timeout=15)
        if not waited or image_path is None:
            print("❌ Timeout esperando o gráfico. E-mail não será enviado.")
            return

    print("📤 Preparando e-mail com gráfico...")

    thread = []

    for email_to in EMAIL_TO:
        msg = MIMEMultipart()
        msg["From"] = EMAIL_FROM
        msg["To"] = email_to  # Atribuindo um e-mail por vez ao campo "To"
        msg["Subject"] = "Gráfico de Cotações"
        msg.attach(MIMEText("Segue o gráfico atualizado.", "plain"))

        try:
            with open(image_path, "rb") as img:
                mime_img = MIMEImage(img.read())
                msg.attach(mime_img)
        except Exception as e:
            print(f"❌ Erro ao anexar imagem: {e}")
            return

        def _send(email, message):
            try:
                with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                    server.starttls()
                    server.login(EMAIL_FROM, EMAIL_PASSWORD)
                    server.send_message(message)
                print(f"✅ E-mail enviado com sucesso para {email}!")
            except Exception as e:
                print(f"❌ Erro ao enviar e-mail para {email}: {e}")

        t = threading.Thread(target=_send, args=(email_to, msg))  # Passando email_to e msg corretamente
        t.start()
        thread.append(t)

    for t in thread:
        t.join()

    # Medindo o tempo total de envio
    end_time = time.time()  # Marca o fim do envio
    duration = end_time - start_time
    print(f"⏱️ Tempo total de envio: {duration:.4f} segundos")


def main():
    inicio = time.time()  # Marca o início

    threads = []

    print("🚀 Iniciando coleta de dados e geração de gráfico...")

    #series = {1: "Dólar (R$)", 21619: "Euro (R$)", 4: "Ouro (R$/g)"}
    series = {
    1: "Dólar (R$)",
    21619: "Euro (R$)",
    4: "Ouro (R$/g)",
    21620: "Libra Esterlina",
    21621: "Franco Suíço",
    21622: "Dólar Canadense",
    21623: "Dólar Australiano",
    21624: "Iene Japonês",
    21625: "Coroa Dinamarquesa",
    21626: "Coroa Norueguesa",
    21627: "Coroa Sueca",
    21628: "Peso Argentino",
    21629: "Peso Chileno",
    21630: "Peso Colombiano",
    21631: "Peso Mexicano",
    21632: "Bolívar Venezuelano",
    21635: "Yuan Chinês",
    21636: "Won Sul-Coreano",
    21637: "Rublo Russo",
    21638: "Lira Turca",
    21639: "Rupia Indiana",
    21640: "Rand Sul-Africano",
    21641: "Ringgit Malaio",
    21642: "Baht Tailandês",
}

    for codigo, nome in series.items():
        t = threading.Thread(target=fetch_bcb_data, args=(codigo, nome))
        threads.append(t)
        t.start()

    t_plot = threading.Thread(target=generate_plot)
    threads.append(t_plot)
    t_plot.start()

    t_email = threading.Thread(target=send_email)
    threads.append(t_email)
    t_email.start()

    for t in threads:
        t.join()

    fim = time.time()  # Marca o fim
    duracao = fim - inicio

    print("🏁 Execução finalizada.")
    print(f"⏱️ Tempo total: {duracao:.4f} segundos", flush=True)

if __name__ == "__main__":
    print("🟢 Chamando main()...")
    main()
    print("🔚 main() terminou")
