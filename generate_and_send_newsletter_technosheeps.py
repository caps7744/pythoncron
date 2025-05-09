from __future__ import print_function
import openai
import requests
import asyncio
from openai import OpenAI
import time
import brevo_python
from brevo_python.rest import ApiException
from pprint import pprint
from datetime import datetime, timedelta
import uuid
import os

# === CONFIGURAZIONI ===
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
BREVO_API_KEY = os.environ["BREVO_API_KEY"]

# Configure API key authorization: api-key
configuration = brevo_python.Configuration()
configuration.api_key['api-key'] = BREVO_API_KEY

# create an instance of the API class
api_instance = brevo_python.EmailCampaignsApi(brevo_python.ApiClient(configuration))

# === PASSO 1: Ricerca Web ===
def fetch_news():

    client = OpenAI(
        api_key=OPENAI_API_KEY
    )

    response = client.responses.create(
        model="gpt-4.1",
        tools=[{"type": "web_search_preview"}],
        input= ("Search for last week 10 most interesting tech news, give me the urls. "
            " Make sure that the news are from last week, not before. "
            " Please respond with a list of ulrs only, without comments or other things.")
    )

    return response.output_text

# === PASSO 2: Sintesi tramite Agent ===
def summarize_news_with_agent(urls):
    client = OpenAI(
        api_key=OPENAI_API_KEY
    )

    url_template = "https://technosheeps.com/assets/template01.html"
    response_template = requests.get(url_template)
    html_template = response_template.text

    prompt = (
    "You must take a text input that contains some urls and a html template. "
    "Each url is a tech news and you should obtain the news title and a short summarized content of about 100 words for each news. "
    "Then you should put all the news you gathered inside the template. Change only the news and leave the rest as is. "
    "Please respond with the html only, without comments or other things. "
    "Here is your input urls: " + urls + ". Here is your input template: " + html_template
    )

    response = client.responses.create(
        model="gpt-4.1",
        input=prompt
    )

    resp_text = response.output_text

    resp_text = resp_text[resp_text.find("<!DOCTYPE html>"):]
    resp_text = resp_text.split("</html>", 1)[0] + "</html>"

    return resp_text

# === PASSO 4: Invio via MailerLite ===
def send_newsletter(html_content):

    now = datetime.now() + timedelta(minutes = 2)
    send_time = now.strftime("%Y-%m-%d %H:%M:%S")
    print(send_time)

    now_date = now.strftime("%m/%d")

    myId = uuid.uuid4()

    email_campaigns = brevo_python.CreateEmailCampaign(
        name= "Campaign " + str(myId),
        subject= "Technosheeps Newsletter " + now_date,
        sender= { "name": "Technosheeps", "email": "newsletter@technosheeps.com"},
        html_content=html_content,
        recipients= {"listIds": [2]},
        scheduled_at=send_time
    )

    try:
        api_response = api_instance.create_email_campaign(email_campaigns)
        pprint(api_response)
    except ApiException as e:
        print("Exception when callingoiuh: %s\n" % e)

# === ESECUZIONE ===
def doNewsletter():
    news_urls = fetch_news()
    html = summarize_news_with_agent(news_urls)
    send_newsletter(html)

if __name__ == "__main__":
    doNewsletter()