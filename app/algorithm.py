from app.views import *
import datetime
import time
from langchain_community.document_loaders import JSONLoader
import csv
from langchain.document_loaders.csv_loader import CSVLoader
from langchain_openai import OpenAIEmbeddings 
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_pinecone import PineconeVectorStore
import os
from langchain_openai import ChatOpenAI
from langchain.chains import ConversationalRetrievalChain 
from langchain.callbacks import get_openai_callback
import random
from langchain_core.prompts.chat import SystemMessagePromptTemplate
from langchain.prompts.chat import HumanMessagePromptTemplate
from langchain_core.prompts.chat import ChatPromptTemplate

general_system_template = r""" 
Tu es un agent commercial très doué chargé de faire vendre le produit decrit en contexte. Pas de reponse trop longue ou hors du contexte. Et quand la reponse est négative essaie de lui presenter d'autres avantages ou si possible la reduction sur le prix disponible. Ton seul but est qu'il decide d'acheter
----
{context}
----
"""
general_user_template = "Question:```{question}```"
messages = [
            SystemMessagePromptTemplate.from_template(general_system_template),
            HumanMessagePromptTemplate.from_template(general_user_template)
]
qa_prompt = ChatPromptTemplate.from_messages( messages )
 
INDEX_NAME = os.environ.get('PINECONE_INDEX')


def convertir_en_csv(liste_dico, nom_fichier):
  
  with open(nom_fichier, "w", newline="") as fichier_csv:
    # Créer un objet DictWriter pour écrire le fichier CSV.
    writer = csv.DictWriter(fichier_csv, fieldnames=["question", "reponse"], extrasaction=False)

    # Écrire chaque dictionnaire de la liste dans le fichier CSV.
    for dico in liste_dico:
      writer.writerow(dico)


def store_embedding0( user : User) :
    embs = json.loads(user.text_info)
    fic = f'seller_{user.pk}.csv'
    convertir_en_csv(embs, fic)
    loader = CSVLoader(file_path=fic)
    documents = loader.load()
    embeddings_model = OpenAIEmbeddings()
    docsearch = PineconeVectorStore.from_documents(documents, embeddings_model, index_name = INDEX_NAME)


    

def store_embedding( user : User) :
    text = user.text_info
    embeddings_model = OpenAIEmbeddings()
    text_splitter = RecursiveCharacterTextSplitter(
            # Set a really small chunk size, just to show.
            chunk_size=500,
            chunk_overlap=120,
            length_function=len,
            is_separator_regex=False,
    )
    texts = text_splitter.split_text(text)
    docsearch = PineconeVectorStore.from_texts(texts, embeddings_model, index_name=INDEX_NAME, namespace = f'seller{user.pk}')


def send_message_to_ai(ai_chat : AIChat, user : User) :
    embeddings_model = OpenAIEmbeddings()
    vectorstore = PineconeVectorStore(
        index_name=INDEX_NAME,
        embedding=embeddings_model,
    )
    llm_model = ChatOpenAI()
    chain = ConversationalRetrievalChain.from_llm(llm=llm_model, retriever=vectorstore.as_retriever(
       search_kwargs={'filter': {'source': f'seller_{user.pk}.csv', "k": 5}}, chain_type="stuff", 
       combine_docs_chain_kwargs={'prompt': qa_prompt}
    ))
    with get_openai_callback() as cb:
        response = chain.invoke({"question": ai_chat.sent, "chat_history": ai_chat.get_history()})
        ai_chat.received = response['answer']
        ai_chat.save()
        rep_message = Message.objects.get(old_pk = ai_chat.unique_id)
        message = Message.objects.create( room = ai_chat.room, text = response['answer'], user = user, old_pk = random.randint(-1, -100000000), reply = json.dumps({
            'author' : rep_message.user,
            'typ' : 'text',
            'content' : ai_chat.sent
        }) )
        

    ai_chat.cost = cb.total_cost
    ai_chat.save()



    


def response_to(mes : Message) :
    aichat = AIChat.objects.create(unique_id = mes.old_pk, sent = mes.text, room = mes.room )
    def send_ai() :
        send_message_to_ai(ai_chat = aichat, user=mes.room.users.exclude(pk = mes.user).first())
    send_by_thread(send_ai)
    while not AIChat.objects.get(unique_id = mes.old_pk).received :
        channel_layer = get_channel_layer()
        heure_utc = datetime.datetime.now().astimezone(datetime.timezone.utc)
        heure_utc_string = heure_utc.strftime("%Y-%m-%dT%H:%M:%SZ")
        async_to_sync(channel_layer.group_send)(mes.room.slug, {
            'type' : 'g_w',
            'result' : {
                'room' : mes.room.slug,
                'user' : mes.user.pk,
                'last' : heure_utc_string
            }
        })
        time.sleep(0.4)
